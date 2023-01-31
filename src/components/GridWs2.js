import React, { useRef, useState, useEffect, useCallback } from "react";
import './styles/grid2.css';

const Image = ({
  imageData,
  width,
  height,
  user,
  ownersRaw,
  sendMessage,
  webSocket,
  readyState }) => {

  const canvasRef = useRef(null);
  const canvasDiv = useRef(null);
  const tooltipRef = useRef(null);
  const divWidth = width;
  const divHeight = height;
  const [scale, setScale] = useState(1);
  const [owners, setOwners] = useState(Array(width * height).fill(""))

  const handleWheel = useCallback((event) => {
    event.preventDefault();
    const delta = event.deltaY < 0 ? 1.1 : 0.9;
    setScale(scale * delta);
  }, [scale]);

  // useEffect(() => {
  //   canvasRef.current.addEventListener(
  //     "wheel",
  //     handleWheel,
  //     { passive: false }
  //   );
  //   return () => {
  //     canvasRef.current.removeEventListener("wheel", handleWheel);
  //   };
  // }, [handleWheel])
  useEffect(() => {
    console.log(ownersRaw)
    if (ownersRaw){
      const parsedOwners = JSON.parse(ownersRaw);
      setOwners(parsedOwners);
    }
    else {
      setOwners(Array(width * height).fill(""))
    }
  },[ownersRaw])
  useEffect(() => {
    canvasRef.current.style.transform = `scale(${scale})`;
    canvasDiv.current.style.transform = `scale(${scale})`;
  }, [scale]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    const imgData = ctx.createImageData(width, height);
    const parsedGrid = JSON.parse(imageData);
    const data = new Uint8ClampedArray(4096 * 4);
    for (let i = 0; i < 4096; i++) {
      const color = parsedGrid[i];
      const [r, g, b, a] = mapColorToRGBA(color);
      data[i * 4] = r;
      data[i * 4 + 1] = g;
      data[i * 4 + 2] = b;
      data[i * 4 + 3] = a;
    }
    imgData.data.set(data);
    ctx.putImageData(imgData, 0, 0);

  }, [imageData, width, height]);

  const handleClick = (event) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    let x = (event.clientX - rect.left);
    let y = (event.clientY - rect.top);
    x = x < 0 ? 0 : x;
    y = y < 0 ? 0 : y;
    x = x >= height ? height-1 : x;
    y = y >= width ? width-1 : y;
    const ctx = canvas.getContext('2d');
    const imageData = ctx.getImageData(x, y, 1, 1).data;

    if (readyState === 1) {
      webSocket.send(JSON.stringify({x:Math.floor(x), y:Math.floor(y), user:user.uid == null ? "NA" : user.displayName}))
    }
  };
  useEffect(() => {

    const canvas = canvasRef.current;
    const tooltip = tooltipRef.current;
    canvas.addEventListener('mousemove', (event) => {
      const rect = canvas.getBoundingClientRect();
      let x = event.clientX - rect.left - 0.5;
      let y = event.clientY - rect.top - 0.5;
      x = x < 0 ? 0 : x;
      y = y < 0 ? 0 : y;
      x = x >= height ? height-1 : x;
      y = y >= width ? width-1 : y;
      const tipx = x+120
      const tipy = y+10
      // Calculate the index of the array based on x and y
      const index = Math.floor(y) * width + Math.floor(x);
      const content = owners[index];

      // Update the content of the tooltip
      tooltip.innerHTML = content;

      // Show the tooltip
      tooltip.style.display = 'block';
      tooltip.style.left = tipx + "px";
      tooltip.style.top = tipy + "px";
      tooltip.style.visibility = content===undefined?"hidden":"visible";
    });

    canvas.addEventListener('mouseout', () => {
      // Hide the tooltip
      tooltip.style.display = 'none';
    });
  }, []);

  return (
    <div
      width={divWidth}
      height={divHeight}
      ref={canvasDiv}
      style={{
        width: 320,
        height: 320,
        overflow: "hidden",
      }}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{
          imageRendering: "pixelated",
          width: {width},
          height: {height}
        }}
        onClick={handleClick}
        />
        <div className="tooltip" ref={tooltipRef}>Tooltip Content</div>
    </div>
  );
};

export default Image;

function mapColorToRGBA(colorValue) {
  return webSafeColors[colorValue];
}

const webSafeColors = [
  [0,0,0,255],
  [0,0,0,255],
  [0,0,0,255],
  [0,0,0,255],
  [0,0,0,255],
  [0,0,0,255],
  [0,0,0,255],
  [0,0,0,255],
  [0,0,0,255],
  [0,0,0,255],
  [0,0,0,255],
  [51,0,0,255],
  [102,0,0,255],
  [153,0,0,255],
  [204,0,0,255],
  [255,0,0,255],
  [0,51,0,255],
  [51,51,0,255],
  [102,51,0,255],
  [153,51,0,255],
  [204,51,0,255],
  [255,51,0,255],
  [0,102,0,255],
  [51,102,0,255],
  [102,102,0,255],
  [153,102,0,255],
  [204,102,0,255],
  [255,102,0,255],
  [0,153,0,255],
  [51,153,0,255],
  [102,153,0,255],
  [153,153,0,255],
  [204,153,0,255],
  [255,153,0,255],
  [0,204,0,255],
  [51,204,0,255],
  [102,204,0,255],
  [153,204,0,255],
  [204,204,0,255],
  [255,204,0,255],
  [0,255,0,255],
  [51,255,0,255],
  [102,255,0,255],
  [153,255,0,255],
  [204,255,0,255],
  [255,255,0,255],
  [0,0,51,255],
  [51,0,51,255],
  [102,0,51,255],
  [153,0,51,255],
  [204,0,51,255],
  [255,0,51,255],
  [0,51,51,255],
  [51,51,51,255],
  [102,51,51,255],
  [153,51,51,255],
  [204,51,51,255],
  [255,51,51,255],
  [0,102,51,255],
  [51,102,51,255],
  [102,102,51,255],
  [153,102,51,255],
  [204,102,51,255],
  [255,102,51,255],
  [0,153,51,255],
  [51,153,51,255],
  [102,153,51,255],
  [153,153,51,255],
  [204,153,51,255],
  [255,153,51,255],
  [0,204,51,255],
  [51,204,51,255],
  [102,204,51,255],
  [153,204,51,255],
  [204,204,51,255],
  [255,204,51,255],
  [0,255,51,255],
  [51,255,51,255],
  [102,255,51,255],
  [153,255,51,255],
  [204,255,51,255],
  [255,255,51,255],
  [0,0,102,255],
  [51,0,102,255],
  [102,0,102,255],
  [153,0,102,255],
  [204,0,102,255],
  [255,0,102,255],
  [0,51,102,255],
  [51,51,102,255],
  [102,51,102,255],
  [153,51,102,255],
  [204,51,102,255],
  [255,51,102,255],
  [0,102,102,255],
  [51,102,102,255],
  [102,102,102,255],
  [153,102,102,255],
  [204,102,102,255],
  [255,102,102,255],
  [0,153,102,255],
  [51,153,102,255],
  [102,153,102,255],
  [153,153,102,255],
  [204,153,102,255],
  [255, 153, 102, 255],
  [0,204,102,255],
  [51,204,102,255],
  [102,204,102,255],
  [153,204,102,255],
  [204,204,102,255],
  [255,204,102,255],
  [0,255,102,255],
  [51,255,102,255],
  [102,255,102,255],
  [153,255,102,255],
  [204,255,102,255],
  [255,255,102,255],
  [0,0,153,255],
  [51,0,153,255],
  [102,0,153,255],
  [153,0,153,255],
  [204,0,153,255],
  [255,0,153,255],
  [0,51,153,255],
  [51,51,153,255],
  [102,51,153,255],
  [153,51,153,255],
  [204,51,153,255],
  [255,51,153,255],
  [0,102,153,255],
  [51,102,153,255],
  [102,102,153,255],
  [153,102,153,255],
  [204,102,153,255],
  [255,102,153,255],
  [0,153,153,255],
  [51,153,153,255],
  [102,153,153,255],
  [153,153,153,255],
  [204,153,153,255],
  [255,153,153,255],
  [0,204,153,255],
  [51,204,153,255],
  [102,204,153,255],
  [153,204,153,255],
  [204,204,153,255],
  [255,204,153,255],
  [0,255,153,255],
  [51,255,153,255],
  [102,255,153,255],
  [153,255,153,255],
  [204,255,153,255],
  [255,255,153,255],
  [0,0,204,255],
  [51,0,204,255],
  [102,0,204,255],
  [153,0,204,255],
  [204,0,204,255],
  [255,0,204,255],
  [0,51,204,255],
  [51,51,204,255],
  [102,51,204,255],
  [153,51,204,255],
  [204,51,204,255],
  [255,51,204,255],
  [0,102,204,255],
  [51,102,204,255],
  [102,102,204,255],
  [153,102,204,255],
  [204,102,204,255],
  [255,102,204,255],
  [0,153,204,255],
  [51,153,204,255],
  [102,153,204,255],
  [153,153,204,255],
  [204,153,204,255],
  [255,153,204,255],
  [0,204,204,255],
  [51,204,204,255],
  [102,204,204,255],
  [153,204,204,255],
  [204,204,204,255],
  [255,204,204,255],
  [0,255,204,255],
  [51,255,204,255],
  [102,255,204,255],
  [153,255,204,255],
  [204,255,204,255],
  [255,255,204,255],
  [0,0,255,255],
  [51,0,255,255],
  [102,0,255,255],
  [153,0,255,255],
  [204,0,255,255],
  [255,0,255,255],
  [0,51,255,255],
  [51,51,255,255],
  [102,51,255,255],
  [153,51,255,255],
  [204,51,255,255],
  [255,51,255,255],
  [0,102,255,255],
  [51,102,255,255],
  [102,102,255,255],
  [153,102,255,255],
  [204,102,255,255],
  [255,102,255,255],
  [0,153,255,255],
  [51,153,255,255],
  [102,153,255,255],
  [153,153,255,255],
  [204,153,255,255],
  [255,153,255,255],
  [0,204,255,255],
  [51,204,255,255],
  [102,204,255,255],
  [153,204,255,255],
  [204,204,255,255],
  [255,204,255,255],
  [0,255,255,255],
  [51,255,255,255],
  [102,255,255,255],
  [153,255,255,255],
  [204,255,255,255],
  [255, 255, 255, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
  [0, 0, 0, 255],
]