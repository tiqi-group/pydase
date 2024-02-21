import React, { useEffect, useRef } from 'react';
import '../App.css';
import { LevelName } from './NotificationsComponent';
import { NumberInputField } from './NumberInputField';

// TODO: add button functionality

export type QuantityObject = {
  type: 'Quantity';
  readonly: boolean;
  value: {
    magnitude: number;
    unit: string;
  };
  doc?: string;
};
export type IntObject = {
  type: 'int';
  readonly: boolean;
  value: number;
  doc?: string;
};
export type FloatObject = {
  type: 'float';
  readonly: boolean;
  value: number;
  doc?: string;
};
export type NumberObject = IntObject | FloatObject | QuantityObject;

type NumberComponentProps = {
  name: string;
  type: 'float' | 'int';
  parentPath?: string;
  value: number;
  readOnly: boolean;
  docString: string;
  isInstantUpdate: boolean;
  unit?: string;
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (
    value: unknown,
    attributeName?: string,
    prefix?: string,
    callback?: (ack: unknown) => void
  ) => void;
  displayName?: string;
  id: string;
};

export const NumberComponent = React.memo((props: NumberComponentProps) => {
  const {
    value,
    readOnly,
    docString,
    isInstantUpdate,
    unit,
    addNotification,
    changeCallback = () => {},
    displayName,
    id
  } = props;

  const renderCount = useRef(0);
  const fullAccessPath = [props.parentPath, props.name]
    .filter((element) => element)
    .join('.');

  useEffect(() => {
    // emitting notification
    let notificationMsg = `${fullAccessPath} changed to ${props.value}`;
    if (unit === undefined) {
      notificationMsg += '.';
    } else {
      notificationMsg += ` ${unit}.`;
    }
    addNotification(notificationMsg);
  }, [props.value]);

  return (
    <div className="component numberComponent" id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <NumberInputField
        name={fullAccessPath}
        value={value}
        displayName={displayName}
        unit={unit}
        readOnly={readOnly}
        type={props.type}
        docString={docString}
        isInstantUpdate={isInstantUpdate}
        changeCallback={changeCallback}
      />
    </div>
  );
});
