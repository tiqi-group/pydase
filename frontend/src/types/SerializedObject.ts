import { QuantityMap } from "./QuantityMap";

interface SignatureDict {
  parameters: Record<string, Record<string, unknown>>;
  return_annotation: Record<string, unknown>;
}

interface SerializedObjectBase {
  full_access_path: string;
  doc: string | null;
  readonly: boolean;
}

type SerializedInteger = SerializedObjectBase & {
  value: number;
  type: "int";
};

type SerializedFloat = SerializedObjectBase & {
  value: number;
  type: "float";
};

type SerializedQuantity = SerializedObjectBase & {
  value: QuantityMap;
  type: "Quantity";
};

type SerializedBool = SerializedObjectBase & {
  value: boolean;
  type: "bool";
};

type SerializedString = SerializedObjectBase & {
  value: string;
  type: "str";
};

export type SerializedEnum = SerializedObjectBase & {
  name: string;
  value: string;
  type: "Enum" | "ColouredEnum";
  enum: Record<string, string>;
};

type SerializedList = SerializedObjectBase & {
  value: SerializedObject[];
  type: "list";
};

type SerializedDict = SerializedObjectBase & {
  value: Record<string, SerializedObject>;
  type: "dict";
};

type SerializedNoneType = SerializedObjectBase & {
  value: null;
  type: "NoneType";
};

type SerializedNoValue = SerializedObjectBase & {
  value: null;
  type: "None";
};

type SerializedMethod = SerializedObjectBase & {
  value: "RUNNING" | null;
  type: "method";
  async: boolean;
  signature: SignatureDict;
  frontend_render: boolean;
};

type SerializedException = SerializedObjectBase & {
  name: string;
  value: string;
  type: "Exception";
};

type DataServiceTypes = "DataService" | "Image" | "NumberSlider" | "DeviceConnection";

type SerializedDataService = SerializedObjectBase & {
  name: string;
  value: Record<string, SerializedObject>;
  type: DataServiceTypes;
};

export type SerializedObject =
  | SerializedBool
  | SerializedFloat
  | SerializedInteger
  | SerializedString
  | SerializedList
  | SerializedDict
  | SerializedNoneType
  | SerializedMethod
  | SerializedException
  | SerializedDataService
  | SerializedEnum
  | SerializedQuantity
  | SerializedNoValue;
