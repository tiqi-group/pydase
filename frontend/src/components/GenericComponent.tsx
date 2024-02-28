import React, { useContext } from 'react';
import { ButtonComponent } from './ButtonComponent';
import { NumberComponent } from './NumberComponent';
import { SliderComponent } from './SliderComponent';
import { EnumComponent } from './EnumComponent';
import { MethodComponent } from './MethodComponent';
import { AsyncMethodComponent } from './AsyncMethodComponent';
import { StringComponent } from './StringComponent';
import { ListComponent } from './ListComponent';
import { DataServiceComponent, DataServiceJSON } from './DataServiceComponent';
import { DeviceConnectionComponent } from './DeviceConnection';
import { ImageComponent } from './ImageComponent';
import { ColouredEnumComponent } from './ColouredEnumComponent';
import { LevelName } from './NotificationsComponent';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { WebSettingsContext } from '../WebSettings';
import { setAttribute } from '../socket';

type AttributeType =
  | 'str'
  | 'bool'
  | 'float'
  | 'int'
  | 'Quantity'
  | 'list'
  | 'method'
  | 'DataService'
  | 'DeviceConnection'
  | 'Enum'
  | 'NumberSlider'
  | 'Image'
  | 'ColouredEnum';

type ValueType = boolean | string | number | Record<string, unknown>;
export type SerializedValue = {
  type: AttributeType;
  value?: ValueType | ValueType[];
  readonly: boolean;
  doc?: string | null;
  async?: boolean;
  frontend_render?: boolean;
  enum?: Record<string, string>;
};
type GenericComponentProps = {
  attribute: SerializedValue;
  name: string;
  parentPath: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
};

export const GenericComponent = React.memo(
  ({
    attribute,
    name,
    parentPath,
    isInstantUpdate,
    addNotification
  }: GenericComponentProps) => {
    const fullAccessPath = [parentPath, name].filter((element) => element).join('.');
    const id = getIdFromFullAccessPath(fullAccessPath);
    const webSettings = useContext(WebSettingsContext);
    let displayName = name;

    if (webSettings[fullAccessPath] && webSettings[fullAccessPath].displayName) {
      displayName = webSettings[fullAccessPath].displayName;
    }

    function changeCallback(
      value: unknown,
      attributeName: string = name,
      prefix: string = parentPath,
      callback: (ack: unknown) => void = undefined
    ) {
      setAttribute(attributeName, prefix, value, callback);
    }

    if (attribute.type === 'bool') {
      return (
        <ButtonComponent
          name={name}
          parentPath={parentPath}
          docString={attribute.doc}
          readOnly={attribute.readonly}
          value={Boolean(attribute.value)}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === 'float' || attribute.type === 'int') {
      return (
        <NumberComponent
          name={name}
          type={attribute.type}
          parentPath={parentPath}
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
    } else if (attribute.type === 'Quantity') {
      return (
        <NumberComponent
          name={name}
          type="float"
          parentPath={parentPath}
          docString={attribute.doc}
          readOnly={attribute.readonly}
          value={Number(attribute.value['magnitude'])}
          unit={attribute.value['unit']}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === 'NumberSlider') {
      return (
        <SliderComponent
          name={name}
          parentPath={parentPath}
          docString={attribute.value['value'].doc}
          readOnly={attribute.readonly}
          value={attribute.value['value']}
          min={attribute.value['min']}
          max={attribute.value['max']}
          stepSize={attribute.value['step_size']}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === 'Enum') {
      return (
        <EnumComponent
          name={name}
          parentPath={parentPath}
          docString={attribute.doc}
          value={String(attribute.value)}
          readOnly={attribute.readonly}
          enumDict={attribute.enum}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === 'method') {
      if (!attribute.async) {
        return (
          <MethodComponent
            name={name}
            parentPath={parentPath}
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
            name={name}
            parentPath={parentPath}
            docString={attribute.doc}
            value={attribute.value as Record<string, string>}
            addNotification={addNotification}
            displayName={displayName}
            id={id}
            render={attribute.frontend_render}
          />
        );
      }
    } else if (attribute.type === 'str') {
      return (
        <StringComponent
          name={name}
          value={attribute.value as string}
          readOnly={attribute.readonly}
          docString={attribute.doc}
          parentPath={parentPath}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === 'DataService') {
      return (
        <DataServiceComponent
          name={name}
          props={attribute.value as DataServiceJSON}
          parentPath={parentPath}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === 'DeviceConnection') {
      return (
        <DeviceConnectionComponent
          name={name}
          props={attribute.value as DataServiceJSON}
          parentPath={parentPath}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          displayName={displayName}
          id={id}
        />
      );
    } else if (attribute.type === 'list') {
      return (
        <ListComponent
          name={name}
          value={attribute.value as SerializedValue[]}
          docString={attribute.doc}
          parentPath={parentPath}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          id={id}
        />
      );
    } else if (attribute.type === 'Image') {
      return (
        <ImageComponent
          name={name}
          parentPath={parentPath}
          docString={attribute.value['value'].doc}
          displayName={displayName}
          id={id}
          addNotification={addNotification}
          // Add any other specific props for the ImageComponent here
          value={attribute.value['value']['value'] as string}
          format={attribute.value['format']['value'] as string}
        />
      );
    } else if (attribute.type === 'ColouredEnum') {
      return (
        <ColouredEnumComponent
          name={name}
          parentPath={parentPath}
          docString={attribute.doc}
          value={String(attribute.value)}
          readOnly={attribute.readonly}
          enumDict={attribute.enum}
          addNotification={addNotification}
          changeCallback={changeCallback}
          displayName={displayName}
          id={id}
        />
      );
    } else {
      return <div key={name}>{name}</div>;
    }
  }
);
