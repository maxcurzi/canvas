import React, { useRef, useState, useEffect, useCallback } from "react";

const Image = ({ imageData, width, height }) => {
  const canvasRef = useRef(null);
  const canvasDiv = useRef(null);
  const divWidth = width;
  const divHeight = height;
  const [scale, setScale] = useState(1);


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
    canvasRef.current.style.transform = `scale(${scale})`;
    canvasDiv.current.style.transform = `scale(${scale})`;
  }, [scale]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.msImageSmoothingEnabled = false;
    ctx.mozImageSmoothingEnabled = false;
    const imgData = ctx.createImageData(width, height);
    const parsedGrid = JSON.parse(imageData);
    const data = new Uint8ClampedArray(4096 * 4);
    for (let i = 0; i < 4096; i++) {
      const color = parsedGrid[i];
      data[i * 4] = 0;
      data[i * 4 + 1] = color;
      data[i * 4 + 2] = 0;
      data[i * 4 + 3] = 255;
    }
    imgData.data.set(data);
    ctx.putImageData(imgData, 0, 0);

  }, [imageData, width, height]);

  const handleClick = (event) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / 5;
    const y = (event.clientY - rect.top) / 5;
    const ctx = canvas.getContext('2d');
    const imageData = ctx.getImageData(x, y, 1, 1).data;

    console.log(x, y, imageData);
  };


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
        <p>Scale: {scale}</p>
    </div>
  );
};

export default Image;