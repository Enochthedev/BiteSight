import React from "react";
import Svg, {
  Defs,
  LinearGradient,
  Stop,
  Text as SvgText,
  ClipPath,
  Polygon,
  G,
} from "react-native-svg";

interface Props {
  children: string;
  size?: number;
  style?: any;
}

export default function DiamondGradientText({ children, size = 34, style }: Props) {
  const svgHeight = size * 2;
  const svgWidth = 300; // fixed width for now; adjust or make dynamic
  const centerX = svgWidth / 2;
  const centerY = svgHeight / 2;

  // Diamond size relative to font size
  const diamondWidth = svgWidth * 0.3;
  const diamondHeight = size * 1.2;

  const points = `
    ${centerX},${centerY - diamondHeight / 2}
    ${centerX + diamondWidth / 2},${centerY}
    ${centerX},${centerY + diamondHeight / 2}
    ${centerX - diamondWidth / 2},${centerY}
  `;

  return (
    <Svg height={svgHeight} width={svgWidth} style={style}>
      <Defs>
        {/* ClipPath using the text */}
        <ClipPath id="textClip">
          <SvgText
            fontSize={size}
            x={centerX}
            y={centerY}
            textAnchor="middle"
            alignmentBaseline="middle"
            fontFamily="Nunito-ExtraBold"
          >
            {children}
          </SvgText>
        </ClipPath>

        {/* Gradient for purple fill */}
        <LinearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <Stop offset="0%" stopColor="#764C8D" />
          <Stop offset="100%" stopColor="#764C8D" />
        </LinearGradient>
      </Defs>

      {/* Base text in blue */}
      <SvgText
        fill="#4C708D"
        fontSize={size}
        x={centerX}
        y={centerY}
        textAnchor="middle"
        alignmentBaseline="middle"
        fontFamily="Nunito-ExtraBold"
      >
        {children}
      </SvgText>

      {/* Diamond jewel applied once across the whole word */}
      <G clipPath="url(#textClip)">
        {/* Purple fill inside diamond */}
        <Polygon points={points} fill="url(#purpleGrad)" />
        {/* Orange outline */}
        <Polygon
          points={points}
          fill="none"
          stroke="#8A8D4C"
          strokeWidth={size * 0.08}
        />
      </G>
    </Svg>
  );
}
