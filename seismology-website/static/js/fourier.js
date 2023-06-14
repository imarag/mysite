let uploadFileButton = document.querySelector("#upload-file-button");
let uploadFileInput = document.querySelector("#upload-file-input");
let uploadAnotherFileButton = document.querySelector("#upload-another-file-button");
let uploadAnotherFileInput = document.querySelector("#upload-another-file-input");

let uploadSection = document.querySelector("#upload-section");
let graphSection = document.querySelector("#graph-section");

let signalWindowLeftSideSlider = document.querySelector("#signal-window-left-side-slider");
let noiseWindowRightSideSlider = document.querySelector("#noise-window-right-side-slider");
let addNoiseButton = document.querySelector("#add-noise-button");
let removeNoiseButton = document.querySelector("#remove-noise-button");
let wholeSignalButton = document.querySelector("#whole-signal-button");
let windowLengthSlider = document.querySelector("#window-length-slider");
let signalLeftSideBadge = document.querySelector("#signal-left-side-badge");

let downloadGraphButton = document.querySelector("#download-graph-button");
let downloadDataButton = document.querySelector("#download-data-button");

// let signalLeftSideInput = document.querySelector("#signal-left-side-input");
// let windowLengthInput = document.querySelector("#window-length-input");
// let noiseRightSideInput = document.querySelector("#noise-right-side-input");

let windowLengthBadge = document.querySelector("#window-length-badge");
let noiseRightSideBadge = document.querySelector("#noise-right-side-badge");
let noiseTransitionedDiv = document.querySelector("#noise-transitioned-div");
let computeFourierButton = document.querySelector("#computeFourierButton");
let timeSeriesTab = document.querySelector("#time-series-tab");
let fourierTab = document.querySelector("#fourier-tab");
let UploadTab = document.querySelector("#upload-tab");
let optionsMenu = document.querySelector("#options-menu");
let spinnerDiv = document.querySelector("#spinner-div");
let alertPlaceholder = document.querySelector('#liveAlertPlaceholder')
let loadButton = document.querySelector("#load-button");

let fourierDataList;

spinnerDiv.style.display = 'none';


downloadGraphButton.addEventListener('click', function() {
    Plotly.downloadImage('fourier-graph', {
        format: 'png',
        filename: 'plotly_graph',
        width: 800,
        height: 500,
        scale: 1,
        data: fourierDataList
      });
  });


downloadDataButton.addEventListener('click', function() {
    fetch('/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(fourierDataList)
    })
    .then(response => response.blob())
    .then(blob => {
        var link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'fourier_data.xlsx';

        document.body.appendChild(link);
        link.click();

        document.body.removeChild(link);
    });
  });

loadButton.addEventListener('click', () => {
    uploadSection.style.display = 'none';
    graphSection.style.display = 'block';
    spinnerDiv.style.display = 'block';
    fetch('/load-test-mseed-file')
    .then(response => { 
        if (response.ok) {
            return response.json();
        }
        else {
            return response.json().then(data => {
                alert('Error: ' + data['error-message']);
                throw new Error(data['error-message']);
            })
        }
    })
    .then(mseedData => {
        if (mseedData['warning-message']) {
            alert('Warning: ' + mseedData['warning-message']);
        }
        
        let convertedMseedData = prepareTracesList(mseedData);
        initializeParameters();
        createNewPlot(convertedMseedData);
        spinnerDiv.style.display = 'none';
        
    })
    .catch(error => {
        // Handle any errors during the upload process
        console.error('Error uploading MSeed file:', error);
    });
});



const alert = (message, type) => {
  const wrapper = document.createElement('div')
  wrapper.innerHTML = [
    `<div class="alert alert-${type} alert-dismissible" role="alert">`,
    `   <div>${message}</div>`,
    '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
    '</div>'
  ].join('')

  alertPlaceholder.append(wrapper)
}

let signalWindowColor = "rgba(255, 0, 0, 0.3)";
let noiseWindowColor = "rgba(4, 0, 241, 0.3)";

let config;
let layout;
let minXValueTotal;
let maxXValueTotal;
let minYValueTotal;
let maxYValueTotal;
    
let totalTraces;

let noiseWindowAdded = false;


computeFourierButton.addEventListener('click', () => {
    
    fourierTab.disabled = false;
    calculateFourier();
});

timeSeriesTab.addEventListener('click', () => {
    optionsMenu.style.display = 'block';
})

fourierTab.addEventListener('click', () => {
    optionsMenu.style.display = 'none';
})

UploadTab.addEventListener('click', () => {
    optionsMenu.style.display = 'none';
})



uploadFileButton.addEventListener('click', function() {
    uploadFileInput.click();
});

uploadAnotherFileButton.addEventListener('click', function() {
    uploadAnotherFileInput.click();
});


uploadAnotherFileInput.addEventListener('change', function(event) {
    uploadMseedFile()
})

uploadFileInput.addEventListener('change', function(event) {
    uploadMseedFile()
})


function uploadMseedFile() {
    uploadSection.style.display = 'none';
    graphSection.style.display = 'block';

    let mseedFile = uploadFileInput.files[0];
    
    const chunkSize = 1024 * 1024;
    let offset = 0;

        // Create a new FormData object
    const formData = new FormData();

    formData.append('file', mseedFile);
    formData.append('view-page', 'fourier');
    spinnerDiv.style.display = 'block';
    fetch('/upload-mseed-file', {
        method: 'POST',
        body: formData
      })
    .then(response => { 
        if (response.ok) {
            return response.json();
        }
        else {
            return response.json().then(data => {
                alert('Error: ' + data['error-message']);
                throw new Error(data['error-message']);
            })
        }
    })
    .then(mseedData => {
        if (mseedData['warning-message']) {
            alert('Warning: ' + mseedData['warning-message']);
        }
        
        let convertedMseedData = prepareTracesList(mseedData);
        initializeParameters();
        createNewPlot(convertedMseedData);
        spinnerDiv.style.display = 'none';
    })
    .catch(error => {
        // Handle any errors during the upload process
        console.error('Error uploading MSeed file:', error);
    });
}




function initializeParameters() {
    
    config = {
        scrollZoom: true,
        responsive: true,
        displayModeBar: true,
        modeBarButtons: [['pan2d', 'zoom2d', 'resetScale2d', 'resetViews', 'toggleSpikelines']]
    };
    
    layout = {
        title: '',
        margin: {
            l: 0, // left margin
            r: 0, // right margin
            t: 0, // top margin
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
            size: 20 // Adjust the font size as desired
            },
        }
    }; 
}


function createNewPlot(tracesList) {
    let subplotIndex = 1;
    totalTraces = tracesList.length;
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

    
    let startingSignalLeftSide = maxXValueTotal / 8;
    let startingWindowLength = maxXValueTotal / 10;
    signalLeftSideBadge.textContent = `${startingSignalLeftSide.toFixed(0)} sec`;
    windowLengthBadge.textContent = `${startingWindowLength.toFixed(0)} sec`;
    
    // signalLeftSideInput.value = startingSignalLeftSide.toFixed(2);
    // windowLengthInput.value = startingWindowLength.toFixed(2);
    
    
    
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
                fillcolor: signalWindowColor,
                line: {
                    color: 'red',
                    width: 2,
                },
                customdata: 'signal'
            }
        );


        subplotIndex += 1;
    }

    
    
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
    let signalLeftValue = Number(signalWindowLeftSideSlider.value);

    let shapesSignal = layout.shapes.filter(shp => shp.customdata === 'signal');

    for (shp of shapesSignal) {
        shp['x0'] = signalLeftValue;
        shp['x1'] = signalLeftValue + Number(windowLengthSlider.value);
    }
    signalLeftSideBadge.textContent = `${signalLeftValue.toFixed(0)} sec`;
    // signalLeftSideInput.value = signalLeftValue.toFixed(2);


    Plotly.update('time-series-graph', {}, layout);
})


windowLengthSlider.addEventListener('input', function() {
    let signalLeftValue = Number(signalWindowLeftSideSlider.value);
    let windowLengthValue = Number(windowLengthSlider.value);
    windowLengthBadge.textContent = `${windowLengthValue.toFixed(0)} sec`;
    // windowLengthInput.value = windowLengthValue.toFixed(2);
    let shapesSignal = layout.shapes.filter(shp => shp.customdata === 'signal');

    for (shp of shapesSignal) {
        shp['x1'] = signalLeftValue + windowLengthValue;
    }

    if (noiseWindowAdded) {
        let shapesNoise = layout.shapes.filter(shp => shp.customdata === 'noise');
        let noiseRightValue = Number(noiseWindowRightSideSlider.value);
        for (shp of shapesNoise) {
            shp['x0'] = noiseRightValue - windowLengthValue;
        }
    }

    Plotly.update('time-series-graph', {}, layout);
})


wholeSignalButton.addEventListener('click', () => {
    for (shp of layout.shapes) {
        shp['x0'] = minXValueTotal;
        shp['x1'] = maxXValueTotal;
    }
    windowLengthSlider.value = maxXValueTotal - minXValueTotal;
    signalWindowLeftSideSlider.value = minXValueTotal;
    signalLeftSideBadge.textContent = `${minXValueTotal.toFixed(0)} sec`;
    windowLengthBadge.textContent = `${(maxXValueTotal - minXValueTotal).toFixed(0)} sec`;
    Plotly.update('time-series-graph', {}, layout);
})


addNoiseButton.addEventListener('click', () => {
    noiseWindowAdded = true;
    wholeSignalButton.disabled = true;
    addNoiseButton.disabled = true;
    noiseTransitionedDiv.classList.add('active');
    removeNoiseButton.style.display = 'inline';

    let subplotIndex = 1;
    let windowLengthValue = Number(windowLengthSlider.value);
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
                fillcolor: noiseWindowColor,
                line: {
                    color: 'red',
                    width: 2
                },
                customdata: 'noise'
                
            }
        );
        subplotIndex += 1;
    }

    noiseWindowRightSideSlider.min = minXValueTotal;
    noiseWindowRightSideSlider.max = maxXValueTotal;
    noiseWindowRightSideSlider.step = 1;
    noiseWindowRightSideSlider.value = maxXValueTotal / 8;
    noiseRightSideBadge.textContent = `${Number(noiseWindowRightSideSlider.value).toFixed(0)} sec`;
    // noiseRightSideInput.value = Number(noiseWindowRightSideSlider.value).toFixed(2);

    Plotly.update('time-series-graph', {}, layout);
   
  
})

removeNoiseButton.addEventListener('click', () => {
    noiseWindowAdded = false;
    wholeSignalButton.disabled = false;
    addNoiseButton.disabled = false;
    removeNoiseButton.style.display = 'none';
    noiseTransitionedDiv.classList.remove('active');
    let newLayoutShapes = layout.shapes.filter(shp => shp.customdata != 'noise');
    layout.shapes = newLayoutShapes;
    Plotly.update('time-series-graph', {}, layout);
})


noiseWindowRightSideSlider.addEventListener('input', () => {
    let noiseRightValue = Number(noiseWindowRightSideSlider.value);
    let windowLengthValue = Number(windowLengthSlider.value);
    noiseRightSideBadge.textContent = `${noiseRightValue.toFixed(0)} sec`;
    // noiseRightSideInput.value = noiseRightValue.toFixed(2);

    let shapesNoise= layout.shapes.filter(shp => shp.customdata === 'noise');

    for (shp of shapesNoise) {
        shp['x1'] = noiseRightValue;
        shp['x0'] = noiseRightValue - windowLengthValue;
    }
    Plotly.update('time-series-graph', {}, layout);
})


function prepareTracesList(mseedDataObject) {
    let xData;
    let yData;
    let tracesList = [];
    let metr = 1;
    
    let colors = ['#FFF256', '#6495ED', '#FF5677', '#DAF7A6', '#FFFFFF']

    for (tr in mseedDataObject) {
        tracesList.push(
            { 
                x: mseedDataObject[tr]['xdata'], 
                y: mseedDataObject[tr]['ydata'], 
                type: 'scatter', 
                mode: 'lines', 
                name: `Channel: ${mseedDataObject[tr]['stats']['channel']}` , 
                xaxis:`x${metr}`, 
                yaxis: `y${metr}`,
                line: {color: colors[metr-1], width: 1}
            }
        );
        metr += 1;
    };
    return tracesList;
}




function calculateFourier() {
    let fourierFetchURL = `/compute-fourier?signal-window-left-side=${signalWindowLeftSideSlider.value}&window-length=${windowLengthSlider.value}&noise-selected=${noiseWindowAdded}&noise-window-right-side=${noiseWindowRightSideSlider.value}`;
    fetch(fourierFetchURL)
    .then(response => { 
        if (response.ok) {
            return response.json();
        }
        else {
            return response.json().then(data => {
                alert(data['error-message'], 'danger')
                throw new Error(data['error-message']);
            })
        }
    })
    .then(fourierData => {
        alert('The Fourier Spectra has succesfully been calculated. Check the "Fourier Spectra" tab above. ', 'success')
        plotFourierData(fourierData)


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
    let totalTracesFourier = 0;
    let metrColors = 0;

    for (tr in fourierData) {
        let trace_dict = fourierData[tr];
        totalTracesFourier += 1;
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

    let configFourier = {
        scrollZoom: true,
        responsive: true,
        displayModeBar: true,
        modeBarButtons: [['pan2d', 'zoom2d', 'resetScale2d', 'resetViews', 'toggleSpikelines']]
    };
    
    layoutFourier = {
        title: '',
        margin: {
            l: 0, // left margin
            r: 0, // right margin
            t: 0, // top margin
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
            size: 20 // Adjust the font size as desired
            },
        }
    }; 

    for (let ind=1; ind<=totalTracesFourier; ind++) {

        layoutFourier[`xaxis${ind}`] = {
            type: 'log',
            title: 'Frequency (Hz)',
        }

        layoutFourier[`yaxis${ind}`] = {
            type: 'log',
            title: ' ',
        }
    }


    

    Plotly.newPlot('fourier-graph', fourierDataList, layoutFourier, configFourier);
}




