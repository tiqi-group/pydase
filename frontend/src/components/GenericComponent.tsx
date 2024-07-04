import React, { useContext } from "react";
import { ButtonComponent } from "./ButtonComponent";
import { NumberComponent, NumberObject } from "./NumberComponent";
import { SliderComponent } from "./SliderComponent";
import { EnumComponent, EnumSerialization } from "./EnumComponent";
import { MethodComponent } from "./MethodComponent";
import { AsyncMethodComponent } from "./AsyncMethodComponent";
import { StringComponent } from "./StringComponent";
import { ListComponent } from "./ListComponent";
import { DataServiceComponent, DataServiceJSON } from "./DataServiceComponent";
import { DeviceConnectionComponent } from "./DeviceConnection";
import { ImageComponent } from "./ImageComponent";
import { LevelName } from "./NotificationsComponent";
import { getIdFromFullAccessPath } from "../utils/stringUtils";
import { WebSettingsContext } from "../WebSettings";
import { updateValue } from "../socket";
import { DictComponent } from "./DictComponent";
import { parseFullAccessPath } from "../utils/stateUtils";
import { SerializedObject } from "../types/SerializedObject";

type GenericComponentProps = {
  attribute: SerializedObject;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
};

const getPathFromPathParts = (pathParts: string[]): string => {
  let path = "";
  for (const pathPart of pathParts) {
    if (!pathPart.startsWith("[") && path !== "") {
      path += ".";
    }
    path += pathPart;
  }
  return path;
};

const createDisplayNameFromAccessPath = (fullAccessPath: string): string => {
  const displayNameParts = [];
  const parsedFullAccessPath = parseFullAccessPath(fullAccessPath);
  for (let i = parsedFullAccessPath.length - 1; i >= 0; i--) {
    const item = parsedFullAccessPath[i];
    displayNameParts.unshift(item);
    if (!item.startsWith("[")) {
      break;
    }
  }
  return getPathFromPathParts(displayNameParts);
};

export const GenericComponent = React.memo(
  ({ attribute, isInstantUpdate, addNotification }: GenericComponentProps) => {
    const { full_access_path: fullAccessPath } = attribute;
    const id = getIdFromFullAccessPath(fullAccessPath);
    const webSettings = useContext(WebSettingsContext);

    let displayName = createDisplayNameFromAccessPath(fullAccessPath);

    if (webSettings[fullAccessPath]) {
      if (webSettings[fullAccessPath].display === false) {
        return null;
      }
      if (webSettings[fullAccessPath].displayName) {
        displayName = webSettings[fullAccessPath].displayName;
      }
    }

    function changeCallback(
      value: SerializedObject,
      callback: (ack: unknown) => void = () => {},
    ) {
      updateValue(value, callback);
    }

    if (attribute.type === "bool") {
      return (
        <ButtonComponent
          fullAccessPath={fullAccessPath}
          docString={attribute.doc}
          readOnly={attribute.readonly}
          value={Boolean(attribute.value)}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === "float" || attribute.type === "int") {
      return (
        <NumberComponent
          type={attribute.type}
          fullAccessPath={fullAccessPath}
          docString={attribute.doc}
          readOnly={attribute.readonly}
          value={Number(attribute.value)}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === "Quantity") {
      return (
        <NumberComponent
          type="Quantity"
          fullAccessPath={fullAccessPath}
          docString={attribute.doc}
          readOnly={attribute.readonly}
          value={Number(attribute.value["magnitude"])}
          unit={attribute.value["unit"]}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === "NumberSlider") {
      return (
        <SliderComponent
          fullAccessPath={fullAccessPath}
          docString={attribute.value["value"].doc}
          readOnly={attribute.readonly}
          value={attribute.value["value"] as NumberObject}
          min={attribute.value["min"] as NumberObject}
          max={attribute.value["max"] as NumberObject}
          stepSize={attribute.value["step_size"] as NumberObject}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === "Enum" || attribute.type === "ColouredEnum") {
      return (
        <EnumComponent
          attribute={attribute as EnumSerialization}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === "method") {
      if (!attribute.async) {
        return (
          <MethodComponent
            fullAccessPath={fullAccessPath}
            docString={attribute.doc}
            addNotification={addNotification}
            displayName={displayName}
            id={id}
            render={attribute.frontend_render}
          />
        );
      } else {
        return (
          <AsyncMethodComponent
            fullAccessPath={fullAccessPath}
            docString={attribute.doc}
            value={attribute.value as "RUNNING" | null}
            addNotification={addNotification}
            displayName={displayName}
            id={id}
            render={attribute.frontend_render}
          />
        );
      }
    } else if (attribute.type === "str") {
      return (
        <StringComponent
          fullAccessPath={fullAccessPath}
          value={attribute.value as string}
          readOnly={attribute.readonly}
          docString={attribute.doc}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === "DataService") {
      return (
        <DataServiceComponent
          props={attribute.value as DataServiceJSON}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === "DeviceConnection") {
      return (
        <DeviceConnectionComponent
          fullAccessPath={fullAccessPath}
          props={attribute.value as DataServiceJSON}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === "list") {
      return (
        <ListComponent
          value={attribute.value}
          docString={attribute.doc}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          id={id}
        />
      );
    } else if (attribute.type === "dict") {
      return (
        <DictComponent
          value={attribute.value}
          docString={attribute.doc}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          id={id}
        />
      );
    } else if (attribute.type === "Image") {
      return (
        <ImageComponent
          fullAccessPath={fullAccessPath}
          docString={attribute.value["value"].doc}
          displayName={displayName}
          id={id}
          addNotification={addNotification}
          value={attribute.value["value"]["value"] as string}
          format={attribute.value["format"]["value"] as string}
        />
      );
    } else {
      return <div key={fullAccessPath}>{fullAccessPath}</div>;
    }
  },
);

GenericComponent.displayName = "GenericComponent";
