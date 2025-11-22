import React, { useRef, useState, useEffect } from "react";
import './styles/grid.css';
import webSafeColors from './WebSafeColors'

function mapColorToRGBA(colorValue) {
  return webSafeColors[colorValue];
}
const Grid = ({
  imageData,
  width,
  height,
  owners,
  user,
  isAuthenticated,
  sendMessage,
  readyState }) => {
  const canvasRef = useRef(null);
  const tooltipRef = useRef(null);
  const [lastClickTime, setLastClickTime] = useState(0);
  const [scalingFactor, setScalingFactor] = useState(5);
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;


    const originalWidth = width; // Set the original width of your image here
    const originalHeight = height; // Set the original height of your image here

    // Create a temporary canvas to hold the original image
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = originalWidth;
    tempCanvas.height = originalHeight;
    const tempCtx = tempCanvas.getContext('2d');
    const tempImgData = tempCtx.createImageData(originalWidth, originalHeight);
    const tempData = new Uint8ClampedArray(originalWidth * originalHeight * 4);

    for (let i = 0; i < originalWidth * originalHeight; i++) {
      const color = imageData[i];
      const [r, g, b, a] = mapColorToRGBA(color);
      tempData[i * 4] = r;
      tempData[i * 4 + 1] = g;
      tempData[i * 4 + 2] = b;
      tempData[i * 4 + 3] = a;
    }

    tempImgData.data.set(tempData);

    tempCtx.putImageData(tempImgData, 0, 0);

    // Create a new canvas to hold the scaled-up image
    const scaledCanvas = document.createElement('canvas');
    scaledCanvas.width = originalWidth * scalingFactor;
    scaledCanvas.height = originalHeight * scalingFactor;
    const scaledCtx = scaledCanvas.getContext('2d');

    // Draw the scaled-up image on the new canvas
    scaledCtx.imageSmoothingEnabled = false;
    scaledCtx.drawImage(tempCanvas, 0, 0, originalWidth * scalingFactor, originalHeight * scalingFactor);

    // Draw the new canvas on the main canvas
    ctx.drawImage(scaledCanvas, 0, 0, scaledCanvas.width, scaledCanvas.height);

  }, [imageData, width, height, scalingFactor]);

  const handleClick = (event) => {
    let now_t = Date.now()
    if (now_t - lastClickTime > 200) {

      const canvas = canvasRef.current;
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      let x = (event.clientX - rect.left) / scalingFactor;
      let y = (event.clientY - rect.top) / scalingFactor - 1;

      // Adjust for off-by-one error (happens on some zoom levels)
      x = x < 0 ? 0 : x;
      y = y < 0 ? 0 : y;
      x = x >= width ? width - 1 : x;
      y = y >= height ? height - 1 : y;

      if ((readyState === 1) && isAuthenticated()) {
        sendMessage(JSON.stringify({ x: Math.floor(x), y: Math.floor(y), user: user == null ? "" : user.displayName }))
      }
      setLastClickTime(now_t);
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    const tooltip = tooltipRef.current;
    canvas.addEventListener('mousemove', (event) => {
      const rect = canvas.getBoundingClientRect();
      let x = (event.clientX - rect.left);
      let y = (event.clientY - rect.top);
      const tipx = event.clientX
      const tipy = event.clientY
      // Calculate the index of the array based on x and y
      const index = Math.floor(y / scalingFactor) * width + Math.floor(x / scalingFactor);
      const content = owners[index];
      // Update the content of the tooltip
      tooltip.innerHTML = content;
      // tooltip.innerHTML = Math.floor(x)  +","+ Math.floor(y);

      // Show the tooltip
      tooltip.style.display = 'block';
      tooltip.style.left = tipx + "px";
      tooltip.style.top = tipy + "px";
      tooltip.style.visibility = content === undefined ? "hidden" : "visible";
    }, []);

    canvas.addEventListener('mouseout', () => {
      // Hide the tooltip
      tooltip.style.display = 'none';
    });
  }, [owners, imageData, width, scalingFactor]);

  // Mouse wheel zoom
  useEffect(() => {

    const handleWheel = (event) => {
      event.preventDefault();
      // Determine the direction and amount of the scroll
      const delta = Math.sign(event.deltaY);
      const step = 1;

      // Update the scaling factor based on the scroll
      setScalingFactor((factor) => Math.max(1, Math.min(40, factor - delta * step)));
    };

    window.addEventListener('wheel', handleWheel);

    return () => {
      window.removeEventListener('wheel', handleWheel);
    };
  }, []);

  return (
    <div>
      <canvas
        ref={canvasRef}
        width={width * scalingFactor}
        height={height * scalingFactor}
        style={{
          imageRendering: "pixelated",
        }}
        onClick={handleClick}
      />
      <div className="tooltip" ref={tooltipRef}>Tooltip Content</div>
    </div>
  );
};

export default Grid;
