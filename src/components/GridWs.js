import React, { useRef, useState, useEffect } from "react";
import './styles/grid.css';
import webSafeColors from './WebSafeColors'

function mapColorToRGBA(colorValue) {
  return webSafeColors[colorValue];
}

const Image = ({
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

  useEffect(()=>{
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    const imgData = ctx.createImageData(width, height);
    const data = new Uint8ClampedArray(width * height * 4);
    for (let i = 0; i < width * height; i++) {
      const color = imageData[i];
      const [r, g, b, a] = mapColorToRGBA(color);
      data[i * 4] = r;
      data[i * 4 + 1] = g;
      data[i * 4 + 2] = b;
      data[i * 4 + 3] = a;
    }
    imgData.data.set(data);
    ctx.putImageData(imgData, 0, 0);
  }, [imageData, height, width]);

  const handleClick = (event) => {
    let now_t = Date.now()
    if (now_t - lastClickTime > 1000) {

      const canvas = canvasRef.current;
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      let x = (event.clientX - rect.left);
      let y = (event.clientY - rect.top);

      // Adjust for off-by-one error (happens on some zoom levels)
      x = x < 0 ? 0 : x;
      y = y < 0 ? 0 : y;
      x = x >= height ? height-1 : x;
      y = y >= width ? width-1 : y;

      if ((readyState === 1) && isAuthenticated()){
        sendMessage(JSON.stringify({x:Math.floor(x), y:Math.floor(y), user:user.uid == null ? "NA" : user.displayName}))
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
      const index = Math.floor(y) * width + Math.floor(x);
      const content = owners[index];
      // Update the content of the tooltip
      tooltip.innerHTML = content;
      // tooltip.innerHTML = Math.floor(x)  +","+ Math.floor(y);

      // Show the tooltip
      tooltip.style.display = 'block';
      tooltip.style.left = tipx + "px";
      tooltip.style.top = tipy + "px";
      tooltip.style.visibility = content===undefined?"hidden":"visible";
    },[]);

    canvas.addEventListener('mouseout', () => {
      // Hide the tooltip
      tooltip.style.display = 'none';
    });
  }, [owners, imageData, width]);

  return (
    <div>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{
          imageRendering: "pixelated",
        }}
        onClick={handleClick}
        />
      <div className="tooltip" ref={tooltipRef}>Tooltip Content</div>
    </div>
  );
};

export default Image;
