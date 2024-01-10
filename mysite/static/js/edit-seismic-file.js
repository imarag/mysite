let uploadFileInput = document.querySelector("#upload-file-input");
let headerPlotContainer = document.querySelector("#header-plot-container");
let tracesSelect = document.querySelector("#traces-select");

let stationInput = document.querySelector("#station");
let dateInput = document.querySelector("#date");
let timeInput = document.querySelector("#time");
let samplingRateInput = document.querySelector("#sampling-rate");
let nptsInput = document.querySelector("#npts");
let componentInput = document.querySelector("#component");

// get the spinner div
spinnerDiv = document.querySelector("#spinner-div");

// spinner off
spinnerDiv.style.display = "none";

// display none to the total container
headerPlotContainer.style.display = "none";

// initialize the config and layout of the time series graph
let config = {
  scrollZoom: true,
  responsive: true,
  displayModeBar: true,
  modeBarButtons: [["pan2d", "zoom2d", "resetScale2d", "resetViews"]],
};

// when clicked open the file input
document.querySelector("#upload-file-button").addEventListener("click", () => {
  uploadFileInput.click();
});

// when the change event happends, open the browse window
uploadFileInput.addEventListener("change", (e) => {
  uploadSeismicFile(e);
});

tracesSelect.addEventListener("change", () => {
  getTraceInfo(tracesSelect.value);
});

document.querySelector("#update-trace").addEventListener("click", () => {
  updateHeader(tracesSelect.value);
});

// call this function when the user uploads a file
function uploadSeismicFile(ev) {
  // get all the files
  let files = ev.target.files;

  // if empty return
  if (files.length === 0) {
    return;
  }

  // get the first file
  let seismicFile = files[0];

  // create the formData
  let formData = new FormData();

  // Append the MSeed file to the FormData object
  formData.append("file", seismicFile);

  // activate the spinner
  spinnerDiv.style.display = "block";

  // clear the Input with type "file" so that the user can re-load the same file
  uploadFileInput.value = null;

  // fetch to the upload-seimsic-file in flask and do a POST request
  fetch("/edit-seismic-file/upload-seismic-file", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      // if not ok deactivate the spinner and show the modal message
      if (!response.ok) {
        // deactivate spinner
        spinnerDiv.style.display = "none";

        // get the error json
        return response.json().then((errorMessage) => {
          document.querySelector("#modal-message").textContent =
            errorMessage["error_message"];
          document.querySelector("#modal-title").textContent =
            "An error has occured!";
          document.querySelector("#modal-header").style.backgroundColor = "red";
          document.querySelector("#modal-button-triger").click();
          throw new Error(errorMessage);
        });
      }
      // if ok just return the json response
      return response.json();
    })
    .then((tracesLabelsList) => {
      // deactivate spinner
      spinnerDiv.style.display = "none";

      // display block to the container that contains the header menu and the graph
      headerPlotContainer.style.display = "block";

      tracesSelect.innerHTML = "";

      for (tr of tracesLabelsList) {
        let newOption = document.createElement("option");
        newOption.value = tr;
        newOption.text = tr;
        tracesSelect.appendChild(newOption);
      }

      tracesSelect.value = "trace-1";

      getTraceInfo("trace-1");
    })
    .catch((error) => {
      // Handle any errors during the upload process
      console.error("Error uploading MSeed file:", error);
    });
}

function updateHeader(traceSelected) {
  // create the formData
  let formData = new FormData();

  // Append the MSeed file to the FormData object
  formData.append("trace-selected", traceSelected);
  formData.append("station", stationInput.value);
  formData.append("date", dateInput.value);
  formData.append("time", timeInput.value);
  formData.append("component", componentInput.value);

  // activate the spinner
  spinnerDiv.style.display = "block";

  // fetch to the upload-seimsic-file in flask and do a POST request
  fetch("/edit-seismic-file/update-header", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      // if not ok deactivate the spinner and show the modal message
      if (!response.ok) {
        // deactivate spinner
        spinnerDiv.style.display = "none";

        // get the error json
        return response.json().then((errorMessage) => {
          document.querySelector("#modal-message").textContent =
            errorMessage["error_message"];
          document.querySelector("#modal-title").textContent =
            "An error has occured!";
          document.querySelector("#modal-header").style.backgroundColor = "red";
          document.querySelector("#modal-button-triger").click();
          throw new Error(errorMessage);
        });
      }
      // if ok just return the json response
      return response.json();
    })
    .then((response) => {
      // deactivate spinner
      spinnerDiv.style.display = "none";

      document.querySelector("#modal-message").textContent =
        "You have succesfully updated the seismic parameters of the respective record. Feel free to download the updated seismic file and/or the updated seismic header information, using the <Download File> and the <Download Header> options below the graph, respectively.";
      document.querySelector("#modal-title").textContent =
        "Succesful Header Update";
      document.querySelector("#modal-header").style.backgroundColor = "green";
      document.querySelector("#modal-button-triger").click();
    })
    .catch((error) => {
      // Handle any errors during the upload process
      console.error("Error uploading MSeed file:", error);
    });
}

function getTraceInfo(selectedTrace) {
  fetch(`/edit-seismic-file/get-trace-info?selected-trace=${selectedTrace}`)
    .then((response) => {
      // if not ok deactivate the spinner and show the modal message
      if (!response.ok) {
        // deactivate spinner
        spinnerDiv.style.display = "none";

        // get the error json
        return response.json().then((errorMessage) => {
          document.querySelector("#modal-message").textContent =
            errorMessage["error_message"];
          document.querySelector("#modal-title").textContent =
            "An error has occured!";
          document.querySelector("#modal-header").style.backgroundColor = "red";
          document.querySelector("#modal-button-triger").click();
          throw new Error(errorMessage);
        });
      }
      // if ok just return the json response
      return response.json();
    })
    .then((traceDataObject) => {
      stationInput.value = traceDataObject["stats"]["station"];
      dateInput.value = traceDataObject["stats"]["date"];
      timeInput.value = traceDataObject["stats"]["time"];
      samplingRateInput.value = traceDataObject["stats"]["sampling_rate"];
      nptsInput.value = traceDataObject["stats"]["npts"];
      componentInput.value = traceDataObject["stats"]["channel"];
      let tracePlotObject = {
        x: traceDataObject["xdata"],
        y: traceDataObject["ydata"],
        type: "scatter",
        mode: "lines",
        name: traceDataObject["stats"]["channel"],
        xaxis: `x1`,
        yaxis: `y1`,
        line: { color: "#527bf7", width: 1 },
      };

      let layout = {
        title: "",
        margin: {
          l: 40,
          r: 15,
          t: 40,
          b: 40,
        },
        autosize: true,
        height: 500,
        grid: { rows: 1, columns: 1 },
        plot_bgcolor: "white",
        paper_bgcolor: "white",
        legend: {
          orientation: "h",
          x: 0.5,
          y: 1.15,
          xanchor: "center",
          font: {
            size: 20, // Adjust the font size as desired
          },
        },
      };

      Plotly.newPlot("time-series-graph", [tracePlotObject], layout, config);
    })
    .catch((error) => {
      // Handle any errors during the upload process
      console.error("Error uploading MSeed file:", error);
    });
}
