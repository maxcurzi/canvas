import './styles/grid.css';
import React, { useEffect, useState } from 'react';
import 'react-tooltip/dist/react-tooltip.css';
import { Tooltip } from 'react-tooltip'

const GridWs = (props) =>{
  const [pixelArray, setPixelArray] = useState(Array(props.gridSize * props.gridSize).fill(0))
  const [owners, setOwners] = useState(Array(props.gridSize * props.gridSize).fill(""))
  const [gridSize, setGridSize] = useState(props.gridSize)
  const [lastClickTime, setLastClickTime] = useState(0)
  const [selected, setSelected] = useState(Array(props.gridSize * props.gridSize).fill(false))
  const handleClick = async (x_value, y_value, user_value) => {
    if (props.readyState === 1) {
      props.sendMessage(JSON.stringify({x:x_value, y:y_value, user:user_value}))
    }
  }
  useEffect(() => {
    if (props.gridData) {
      const parsedGrid = JSON.parse(props.gridData);
      setPixelArray(parsedGrid);
    }
    if (props.owners) {
      const parsedOwners = JSON.parse(props.owners)
      setOwners(parsedOwners);
    }
    if (props.gridSize) {
      setGridSize(props.gridSize);
    }
  }, [props.gridData, props.owners, props.gridSize]);

  function changeBackground(index) {
    const newSelected = selected;
    newSelected[index] = true;
    setSelected(newSelected);
  }
  function restoreBackground(index) {
    const newSelected = selected;
    newSelected[index] = false;
    setSelected(newSelected);
  }

  return (
    <div className="grid" style={{
      'gridTemplateColumns': `repeat(${gridSize}, 1fr)`,
      'gridTemplateRows': `repeat(${gridSize}, 1fr)`
    }}>
      {pixelArray.map((pixel, index) => {
        const x = index % gridSize
        const y = Math.floor(index / gridSize)
        const tooltip_text = owners[index] === undefined ? null : "Owner: " + owners[index]
        return <div
          className={`box  ${selected[index]===true?"hovered":`color${pixel}`}`}
          title={tooltip_text}
          onClick={(event) => {
            let now_t = Date.now()
            if ((now_t - lastClickTime > 1) && props.user !== null){
              setLastClickTime(now_t )
              handleClick(x, y, props.user.uid == null ? "NA" : props.user.displayName)
            }
          }}
          onMouseEnter={(e) => { changeBackground(index) }}
          onMouseLeave={(e) => { restoreBackground(index) }}
          key={index}
          data-tooltip-content="hello world"
        />
      })}
    </div>
  );
};

export default GridWs;
