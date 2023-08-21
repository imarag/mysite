// define all the variables
let uploadFileInput = document.querySelector("#upload-file-input");
let uploadAnotherFileInput = document.querySelector("#upload-another-file-input");

let signalLeftSideBadge = document.querySelector("#signal-left-side-badge");
let windowLengthBadge = document.querySelector("#window-length-badge");
let noiseRightSideBadge = document.querySelector("#noise-right-side-badge");

let windowLengthSlider = document.querySelector("#window-length-slider");
let signalWindowLeftSideSlider = document.querySelector("#signal-window-left-side-slider");
let noiseWindowRightSideSlider = document.querySelector("#noise-window-right-side-slider");
let noiseSliderDiv = document.querySelector("#noise-slider-div");

let wholeSignalButton = document.querySelector("#whole-signal-button");
let addNoiseButton = document.querySelector("#add-noise-button");
let removeNoiseButton = document.querySelector("#remove-noise-button");

let timeSeriesTab = document.querySelector("#time-series-tab");
let fourierTab = document.querySelector("#fourier-tab");
let hvsrTab = document.querySelector("#hvsr-tab");

let optionsMenu = document.querySelector("#options-menu");
let spinnerDiv = document.querySelector("#spinner-div");

let vertCompoSelect = document.querySelector("#vertical-component-select");

// display none to some elements
optionsMenu.style.display = 'none';
removeNoiseButton.style.display = 'none';
noiseSliderDiv.style.display = 'none';

// deactivate all tabs initially
fourierTab.disabled = true;
hvsrTab.disabled = true;
timeSeriesTab.disabled = true;

// spinner off
spinnerDiv.style.display = 'none';

// initialize all the parameters that i will use 
////////////////////////////////////////////////////////

// the noise window added is false at the beginning
let noiseWindowAdded = false;

// initialize the config and layout of the time series graph
let config = {
    scrollZoom: true,
    responsive: true,
    displayModeBar: true,
    modeBarButtons: [['pan2d', 'zoom2d', 'resetScale2d', 'resetViews', 'toggleSpikelines']]
};

let layout;

// save here to global variables the total min, max X and Y values
let minXValueTotal;
let maxXValueTotal;
let minYValueTotal;
let maxYValueTotal;

// i want to save to a variable the total traces loaded by the user. It can be 2 or 3
let totalTraces;


////////////////////////////////////////////////////////



// add the click event on the upload-file and another-file-upload buttons
document.querySelector("#upload-file-button").addEventListener('click', function() {
    uploadFileInput.click();
});

document.querySelector("#upload-another-file-button").addEventListener('click', function() {
    uploadAnotherFileInput.click();
});


// add the change event listeners to the input elements
uploadFileInput.addEventListener('change', (ev) => {
    uploadMseedFile(ev)
})

uploadAnotherFileInput.addEventListener('change', (ev) => {
    uploadMseedFile(ev)
})


// when you press the time series tab, display=block for the menu and display=none otherwise
timeSeriesTab.addEventListener('click', () => {
    optionsMenu.style.display = 'block';
    document.querySelector("#upload-file-button").style.display = false;
})

fourierTab.addEventListener('click', () => {
    optionsMenu.style.display = 'none';
    document.querySelector("#upload-file-button").disabled = true;
})

hvsrTab.addEventListener('click', () => {
    optionsMenu.style.display = 'none';
    document.querySelector("#upload-file-button").disabled = true;
})


// add the click event on the calculate the Fourier button and the calculate the HVSR button
document.querySelector("#computeFourierButton").addEventListener('click', calculateFourier);
document.querySelector("#compute-hvsr-button").addEventListener('click', calculateHVSR);


// call this function when the user uploads a file
function uploadMseedFile(ev) {
    // get all the files
    let files = ev.target.files;

    // if empty return
    if (files.length === 0) {
        return;
    }

    // get the first file
    let mseedFile = files[0];

    // create the formData
    let formData = new FormData();

    // Append the MSeed file to the FormData object
    formData.append('file', mseedFile);

    // activate the spinner
    spinnerDiv.style.display = 'block';

    // clear the Input with type "file" so that the user can re-load the same file (both at the uploadInputFile and the another file)
    uploadFileInput.value = null;
    uploadAnotherFileInput.value = null;

    // fetch to the upload-mseed-file in flask and do a POST request
    fetch('/fourier-spectra/upload-mseed-file', {
        method: 'POST',
        body: formData
      })
        .then(response => { 
            // if not ok deactivate the spinner and show the modal message
            if (!response.ok) {
                // deactivate spinner
                spinnerDiv.style.display = 'none';

                // get the error json
                return response.json()
                    .then(errorMessage => {
                        document.querySelector("#modal-message").textContent = errorMessage['error_message'];
                        document.querySelector("#modal-title").textContent = 'An error has occured!'
                        document.querySelector("#modal-header").style.backgroundColor = "red";
                        document.querySelector("#modal-button-triger").click()
                        throw new Error(errorMessage);
                    })
              }
            // if ok just return the json response
            return response.json()
        })
        .then(mseedData => {
            // deactivate spinner
            spinnerDiv.style.display = 'none';

            // display none to the initial "start by upload an mseed file" div
            document.querySelector("#fourier-spectra-start-by-upload-container").style.display = "none";

            // display block to the option menu
            optionsMenu.style.display = 'block';

            // rename the dummy paragraph to have the record name
            document.querySelector("#record-name-paragraph").textContent = mseedData["trace-0"]["record-name"];

            // convert the returned json object to a form that i can use to plot the graph
            let convertedMseedData = prepareTracesList(mseedData);
            
            // initialize some parameters
            initializeParameters();

            // create the plot
            createNewPlot(convertedMseedData);

            // change the option values (the components option in the select element) in the hvsr tab so that 
            // the user can select the channel from the record he uploaded
            // Remove existing options
            vertCompoSelect.innerHTML = "";

            // Add new options (loop through the traces and get the channel)
            let newOptions = [];
            for (tr in mseedData) {
                option = { value: mseedData[tr]["stats"]["channel"], text: mseedData[tr]["stats"]["channel"]};
                newOptions.push(option);
            }
            newOptions.forEach(function(option) {
                let newOption = document.createElement("option");
                newOption.value = option.value;
                newOption.textContent = option.text;
                vertCompoSelect.appendChild(newOption);
              });

            
            
            // disable the other tabs when a new file is uploaded
            fourierTab.disabled = true;
            hvsrTab.disabled = true;
              
          
        })
        .catch(error => {
          // Handle any errors during the upload process
          console.error('Error uploading MSeed file:', error);
        });
}


function prepareTracesList(mseedDataObject) {
    let xData;
    let yData;
    // append here all the traces in an Object form (check below)
    let tracesList = [];
    let metr = 1;

    // define the colors of the record signals
    let colors = ['#FFF256', '#6495ED', '#FF5677', '#DAF7A6', '#FFFFFF']

    for (tr in mseedDataObject) {
        tracesList.push(
            { 
                x: mseedDataObject[tr]['xdata'], 
                y: mseedDataObject[tr]['ydata'], 
                type: 'scatter', 
                mode: 'lines', 
                name: `${mseedDataObject[tr]['stats']['channel']}` , 
                xaxis:`x${metr}`, 
                yaxis: `y${metr}`,
                line: {color: colors[metr-1], width: 1}
            }
        );
        metr += 1;
    };
    return tracesList;
}



function initializeParameters() {
    
    
    
    layout = {
        title: '',
        margin: {
            l: 40,
            r: 15,
            t: 40,
            b: 40
        },
        grid: {rows: 3, columns: 1, pattern: 'independent'},
        plot_bgcolor: '#212529',
        paper_bgcolor: '#212529',
        height: 350,
        shapes: [ ],
        annotations: [],
        legend: {
            orientation: 'h', 
            x: 0.5,           
            y: 1.15,
            xanchor: 'center',
            font: {
            size: 20 // Adjust the font size as desired
            },
        }
    }; 
}


function createNewPlot(tracesList) {
    let subplotIndex = 1;
    totalTraces = tracesList.length;
    // i gather here all the X and Y values to find the min and max to set the limits
    let minMaxXValues = [];
    let minMaxYValues = [];
    for (tr of tracesList) {
        let xArray = tr['x'].map(Number);
        let yArray = tr['y'].map(Number);
        let minXValue = Math.min(...xArray);
        let maxXValue = Math.max(...xArray);
        let minYValue = Math.min(...yArray);
        let maxYValue = Math.max(...yArray);
        minMaxXValues.push(minXValue);
        minMaxXValues.push(maxXValue);
        minMaxYValues.push(minYValue);
        minMaxYValues.push(maxYValue);
    }

    minXValueTotal = Math.min(...minMaxXValues);
    maxXValueTotal = Math.max(...minMaxXValues);
    minYValueTotal = Math.min(...minMaxYValues);
    maxYValueTotal = Math.max(...minMaxYValues);

    // this is how the signal left side and starting window length are gonna be initialized
    let startingSignalLeftSide = maxXValueTotal / 8;
    let startingWindowLength = maxXValueTotal / 10;

    // set the badge
    signalLeftSideBadge.textContent = `${startingSignalLeftSide.toFixed(0)} sec`;
    windowLengthBadge.textContent = `${startingWindowLength.toFixed(0)} sec`;
    
    // create the rectangles (windows)
    for (tr of tracesList) {
        layout.shapes.push(
            {
                type: 'rect',
                x0: startingSignalLeftSide,
                y0: minYValueTotal,
                x1: startingSignalLeftSide + startingWindowLength,
                y1: maxYValueTotal,
                xref:`x${subplotIndex}`, 
                yref: `y${subplotIndex}`,
                fillcolor: "rgba(255, 0, 0, 0.3)",
                line: {
                    color: 'red',
                    width: 2,
                },
                customdata: 'signal'
            }
        );

        subplotIndex += 1;
    }

    
    // set the widgets values
    windowLengthSlider.min = minXValueTotal;
    windowLengthSlider.max = maxXValueTotal;
    windowLengthSlider.step = 1;
    windowLengthSlider.value = startingWindowLength;

    signalWindowLeftSideSlider.min = minXValueTotal;
    signalWindowLeftSideSlider.max = maxXValueTotal;
    signalWindowLeftSideSlider.step = 1;
    signalWindowLeftSideSlider.value = startingSignalLeftSide;
    
    Plotly.newPlot('time-series-graph', tracesList, layout, config);
}




signalWindowLeftSideSlider.addEventListener('input', function() {
    // get its value
    let signalLeftValue = Number(signalWindowLeftSideSlider.value);

    // get the shapes where the customadata is 'signal'
    let shapesSignal = layout.shapes.filter(shp => shp.customdata === 'signal');

    // change the x0 and x1 of the signal shapes
    for (shp of shapesSignal) {
        shp['x0'] = signalLeftValue;
        shp['x1'] = signalLeftValue + Number(windowLengthSlider.value);
    }

    // change the badge
    signalLeftSideBadge.textContent = `${signalLeftValue.toFixed(0)} sec`;

    // update the graph wth the new layout
    Plotly.update('time-series-graph', {}, layout);
})


windowLengthSlider.addEventListener('input', function() {
    // get the value of the signal left side value and its length value
    let signalLeftValue = Number(signalWindowLeftSideSlider.value);
    let windowLengthValue = Number(windowLengthSlider.value);

    // change the badge
    windowLengthBadge.textContent = `${windowLengthValue.toFixed(0)} sec`;

    // get the shapes where the customadata is 'signal'
    let shapesSignal = layout.shapes.filter(shp => shp.customdata === 'signal');

    // change the x1 of the signal shapes
    for (shp of shapesSignal) {
        shp['x1'] = signalLeftValue + windowLengthValue;
    }

    // if the noise window is added then change the noise window length too because the 2 windows need to have the same length
    if (noiseWindowAdded) {
        // get the shapes with customdata noise, get the noise right value and change the x0 of the shapes
        let shapesNoise = layout.shapes.filter(shp => shp.customdata === 'noise');
        let noiseRightValue = Number(noiseWindowRightSideSlider.value);
        for (shp of shapesNoise) {
            shp['x0'] = noiseRightValue - windowLengthValue;
        }
    }

    Plotly.update('time-series-graph', {}, layout);
})


wholeSignalButton.addEventListener('click', () => {
    // if the user selects the whole signal that is to compute the fourier to the whole time series then change the
    // signal length to be the total time series. You cannot use this option when the noise is activated
    for (shp of layout.shapes) {
        shp['x0'] = minXValueTotal;
        shp['x1'] = maxXValueTotal;
    }

    // after you change the shape layout window edges, change also the widgets and teh badges
    windowLengthSlider.value = maxXValueTotal - minXValueTotal;
    signalWindowLeftSideSlider.value = minXValueTotal;
    signalLeftSideBadge.textContent = `${minXValueTotal.toFixed(0)} sec`;
    windowLengthBadge.textContent = `${(maxXValueTotal - minXValueTotal).toFixed(0)} sec`;

    Plotly.update('time-series-graph', {}, layout);
})


addNoiseButton.addEventListener('click', () => {
    // when the noise is added change some parameters
    // noise added true
    noiseWindowAdded = true;

    // disable whole signal button
    wholeSignalButton.disabled = true;

    // disable the add noise button since it is clicked
    addNoiseButton.disabled = true;

    // display block to the noise slider div
    noiseSliderDiv.style.display = "block";

    // display inline to the remove noise
    removeNoiseButton.style.display = 'inline';

    let subplotIndex = 1;
    let windowLengthValue = Number(windowLengthSlider.value);

    // add here the shapes with customdata 'noise'
    for (let i=0; i<totalTraces; i++) {
        layout.shapes.push(
            {
                type: 'rect',
                x0: maxXValueTotal / 8 -  windowLengthValue,
                y0: minYValueTotal,
                x1: maxXValueTotal / 8,
                y1: maxYValueTotal,
                xref:`x${subplotIndex}`, 
                yref: `y${subplotIndex}`,
                fillcolor: "rgba(4, 0, 241, 0.3)",
                line: {
                    color: 'red',
                    width: 2
                },
                customdata: 'noise'
                
            }
        );
        subplotIndex += 1;
    }

    // set the noise slide rof the right window side to the default values
    noiseWindowRightSideSlider.min = minXValueTotal;
    noiseWindowRightSideSlider.max = maxXValueTotal;
    noiseWindowRightSideSlider.step = 1;
    noiseWindowRightSideSlider.value = maxXValueTotal / 8;

    // change also the badge
    noiseRightSideBadge.textContent = `${Number(noiseWindowRightSideSlider.value).toFixed(0)} sec`;

    Plotly.update('time-series-graph', {}, layout);
   
  
})


removeNoiseButton.addEventListener('click', () => {
    // when the user removes the noise
    // noiseWindowAdded false
    noiseWindowAdded = false;

    // wholeSignalButton disabled false (we can use it again)
    wholeSignalButton.disabled = false;

    // add noise button disabled false
    addNoiseButton.disabled = false;

    // remove noise button display none
    removeNoiseButton.style.display = 'none';

    // noiseSliderDiv display none
    noiseSliderDiv.style.display = "none";

    // get all the shapes but those with customdata noise
    let newLayoutShapes = layout.shapes.filter(shp => shp.customdata != 'noise');

    // set the new shapes and update
    layout.shapes = newLayoutShapes;
    Plotly.update('time-series-graph', {}, layout);
})


noiseWindowRightSideSlider.addEventListener('input', () => {
    // when the user changes the window right side of the noise get the value and also the window length slider value
    let noiseRightValue = Number(noiseWindowRightSideSlider.value);
    let windowLengthValue = Number(windowLengthSlider.value);

    // change the badges
    noiseRightSideBadge.textContent = `${noiseRightValue.toFixed(0)} sec`;

    // filter to get only the noise shapes
    let shapesNoise= layout.shapes.filter(shp => shp.customdata === 'noise');

    // change their edges X0, X1
    for (shp of shapesNoise) {
        shp['x1'] = noiseRightValue;
        shp['x0'] = noiseRightValue - windowLengthValue;
    }

    Plotly.update('time-series-graph', {}, layout);
})




function calculateFourier() {
    // if you click on the compute fourier button, make the fourier spectra tab active so the user can click it and see the result
    fourierTab.disabled = false;
    hvsrTab.disabled = false;
    timeSeriesTab.disabled = false;

    // activate the spinner
    spinnerDiv.style.display = 'block';

    // create the fetch url to handle it on the server
    let fourierFetchURL = `/fourier-spectra/compute-fourier?signal-window-left-side=${signalWindowLeftSideSlider.value}&window-length=${windowLengthSlider.value}&noise-selected=${noiseWindowAdded}&noise-window-right-side=${noiseWindowRightSideSlider.value}`;
    
    fetch(fourierFetchURL)
        .then(response => { 
            // if not ok deactivate the spinner and show the modal message
            if (!response.ok) {
                // deactivate spinner
                spinnerDiv.style.display = 'none';

                // return the error as json
                return response.json()
                    .then(errorMessage => {
                        document.querySelector("#modal-message").textContent = errorMessage['error_message'];
                        document.querySelector("#modal-title").textContent = 'An error has occured!'
                        document.querySelector("#modal-header").style.backgroundColor = "red";
                        document.querySelector("#modal-button-triger").click()
                        throw new Error(errorMessage);
                    })
            }
            // if ok just return the json response
            return response.json()
        })
        .then(fourierData => {
            
            // create the fourier graph
            plotFourierData(fourierData)

            // actiate the modal message for a succesful computation
            document.querySelector("#modal-message").textContent = 'The Fourier Spectra has succesfully been calculated. Check the "Fourier Spectra" tab above. ';
            document.querySelector("#modal-title").textContent = 'Succeful calculation!'
            document.querySelector("#modal-header").style.backgroundColor = "green";
            document.querySelector("#modal-button-triger").click()
            
            // deactivate spinner
            spinnerDiv.style.display = 'none';

            // every time you change the windows and recalculate the fourier
            // display none the hvsr graph and reappear it when you click the 
            // calculate graph button
            // do also the same with the download graph and data div 
            document.querySelector("#hvsr-graph").style.display = "none";
            document.querySelector("#graph-data-download-hvsr-div").style.display = "none";
        })
        .catch(error => {
        // Handle any errors during the upload process
        console.error('Error uploading MSeed file:', error);
        });
}

function plotFourierData(fourierData) {

    fourierDataList = [];
    let metrSignalNoise = 1;
    let colors = ['#5E62FF', '#B9BBFF', '#FFF532', '#FDF89E', '#FE4252', '#FBA3AA']
    let metrColors = 0;

    // loop through the traces ({trace0: ... , trace1: ... })
    for (tr in fourierData) {

        // get the trace dict
        let trace_dict = fourierData[tr];

        // loop though the keys of the trace dict. It may have 'signal' or 'signal' and 'noise' if the user selected then noise
        // so this "signal_noise_key" is either 'singal' or 'noise'
        for (signal_noise_key in trace_dict) {
             
            fourierDataList.push(
                { 
                    x: trace_dict[signal_noise_key]['xdata'], 
                    y: trace_dict[signal_noise_key]['ydata'], 
                    type: 'scatter', 
                    mode: 'lines', 
                    name: `${signal_noise_key}, Channel: ${trace_dict[signal_noise_key]['stats']['channel']}` , 
                    xaxis:`x${metrSignalNoise}`, 
                    yaxis: `y${metrSignalNoise}`,
                    line: {color: colors[metrColors], width: 1}
                }
            );
            metrColors +=1;
        }
        metrSignalNoise += 1;
    };

    // define the layout of Fourier
  
    let layoutFourier = {
        title: '',
        margin: {
            l: 0, // left margin
            r: 0, // right margin
            t: 90, // top margin
            b: 0  // bottom margin
        },
        plot_bgcolor: '#212529',
        paper_bgcolor: '#212529',
        height: 500,
        grid: {rows: 3, columns: 1, pattern: 'independent'},
        shapes: [ ],
        annotations: [],
        legend: {
            orientation: 'h', 
            x: 0.5,           
            y: 1.15,
            xanchor: 'center',
            font: {
            size: 12 // Adjust the font size as desired
            },
        }
    }; 

    // loop through the total length of the traces and put log to x and y axis of all the traces
    for (let ind=1; ind<=Object.keys(fourierData).length; ind++) {

        layoutFourier[`xaxis${ind}`] = {
            type: 'log',
            title: 'Frequency (Hz)',
        }

        layoutFourier[`yaxis${ind}`] = {
            type: 'log',
            title: ' ',
        }
    }

    Plotly.newPlot('fourier-graph', fourierDataList, layoutFourier, config);
}



function calculateHVSR(){

    
    // activate the spinner
    spinnerDiv.style.display = 'block';

    // create the fetch url to handle it on the server (pass the selected vertical component)
    let hvsrFetchURL = `/fourier-spectra/compute-hvsr?vertical-component=${vertCompoSelect.value}`;
    
    fetch(hvsrFetchURL)
        .then(response => { 
            // if not ok deactivate the spinner and show the modal message
            if (!response.ok) {
                // deactivate spinner
                spinnerDiv.style.display = 'none';

                return response.json()
                    .then(errorMessage => {
                        document.querySelector("#modal-message").textContent = errorMessage['error_message'];
                        document.querySelector("#modal-title").textContent = 'An error has occured!'
                        document.querySelector("#modal-header").style.backgroundColor = "red";
                        document.querySelector("#modal-button-triger").click()
                        throw new Error(errorMessage);
                    })
            }
            // if ok just return the json response
            return response.json()
        })
        .then(hvsrData => {
            // create the fourier graph
            plotHVSRData(hvsrData)
            
            // deactivate spinner
            spinnerDiv.style.display = 'none';

            // here when you click teh calculate the hvsr button THEN and only then
            // show the hvsr graph and the download graph and data button
            document.querySelector("#hvsr-graph").style.display = "block";
            document.querySelector("#graph-data-download-hvsr-div").style.display = "block";
        })
        .catch(error => {
        // Handle any errors during the upload process
        console.error('Error uploading MSeed file:', error);
        });
}





function plotHVSRData(hvsrData) {

    let hvsrDataList = [
        { 
            x: hvsrData['xdata'], 
            y: hvsrData['ydata'], 
            type: 'scatter', 
            mode: 'lines', 
            name: 'HVSR' , 
            xaxis:'x1', 
            yaxis: 'y1',
            line: {color: '#5E62FF', width: 1}
        }
    ];
    

    // define the layout of HVSR

    let layoutHVSR = {
        title: '',
        margin: {
            l: 0, // left margin
            r: 0, // right margin
            t: 0, // top margin
            b: 0  // bottom margin
        },
        plot_bgcolor: '#212529',
        paper_bgcolor: '#212529',
        height: 300,
        grid: {rows: 3, columns: 1, pattern: 'independent'},
        shapes: [ ],
        annotations: [],
        legend: {
            orientation: 'h', 
            x: 0.5,           
            y: 1.15,
            xanchor: 'center',
            font: {
            size: 12 // Adjust the font size as desired
            },
        },
      
    }; 

    // put log x and y at the 
 
    layoutHVSR['xaxis1'] = {
        type: 'log',
        title: 'Frequency (Hz)',
    }

    layoutHVSR['yaxis1'] = {
        type: 'log',
        title: 'HVSR',
    }


    Plotly.newPlot('hvsr-graph', hvsrDataList, layoutHVSR, config);



    

    
}



