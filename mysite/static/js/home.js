(() => {
  let imageHover = document.querySelector("#image-hover");
  let trimHoverLi = document.querySelector("#trim-hover-li");
  let taperHoverLi = document.querySelector("#taper-hover-li");
  let detrendHoverLi = document.querySelector("#detrend-hover-li");
  let fourierHoverLi = document.querySelector("#fourier-hover-li");
  let PickHoverLi = document.querySelector("#pick-hover-li");

  let recSpans = document.querySelectorAll(".interactive-tools-index-div span");

  for (sp of recSpans) {
    sp.style.display = 'none';
  }

  trimHoverLi.querySelector('span').style.display = 'inline';

  trimHoverLi.addEventListener("mouseover", () => {
    imageHover.src = "/static/img/trim-gif.gif";
    for (sp of recSpans) {
      sp.style.display = 'none';
    }
    trimHoverLi.querySelector('span').style.display = 'inline';
  });
  taperHoverLi.addEventListener("mouseover", () => {
    imageHover.src = "/static/img/taper-gif.gif";
    for (sp of recSpans) {
      sp.style.display = 'none';
    }
    taperHoverLi.querySelector('span').style.display = 'inline';
  });
  detrendHoverLi.addEventListener("mouseover", () => {
    imageHover.src = "/static/img/detrend-gif.gif";
    for (sp of recSpans) {
      sp.style.display = 'none';
    }
    detrendHoverLi.querySelector('span').style.display = 'inline';
  });
  fourierHoverLi.addEventListener("mouseover", () => {
    imageHover.src = "/static/img/fourier-gif.gif";
    for (sp of recSpans) {
      sp.style.display = 'none';
    }
    fourierHoverLi.querySelector('span').style.display = 'inline';
  });
  PickHoverLi.addEventListener("mouseover", () => {
    imageHover.src = "/static/img/pick-gif.gif";
    for (sp of recSpans) {
      sp.style.display = 'none';
    }
    PickHoverLi.querySelector('span').style.display = 'inline';
  });
})();
