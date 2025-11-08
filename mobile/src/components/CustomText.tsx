import React, { ReactNode } from "react";
import { Text, TextProps, StyleProp, TextStyle } from "react-native";

interface CustomTextProps extends TextProps {
  children: ReactNode;             // <-- explicitly type children
  weight?: "regular" | "semi" | "bold";
  style?: StyleProp<TextStyle>;
}

const CustomText: React.FC<CustomTextProps> = ({
  children,
  weight = "regular",
  style,
  ...props
}) => {
  let fontFamily = "Nunito-Regular";
  if (weight === "semi") fontFamily = "Nunito-SemiBold";
  if (weight === "bold") fontFamily = "Nunito-Bold";

  return (
    <Text style={[{ fontFamily }, style]} {...props}>
      {children}
    </Text>
  );
};

export default CustomText;
