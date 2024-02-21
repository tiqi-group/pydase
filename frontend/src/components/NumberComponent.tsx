import React, { useContext, useEffect, useRef } from 'react';
import { WebSettingsContext } from '../WebSettings';
import '../App.css';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
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
  showName?: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (
    value: unknown,
    attributeName?: string,
    prefix?: string,
    callback?: (ack: unknown) => void
  ) => void;
};

export const NumberComponent = React.memo((props: NumberComponentProps) => {
  const {
    name,
    value,
    parentPath,
    readOnly,
    docString,
    isInstantUpdate,
    unit,
    addNotification,
    changeCallback = () => {}
  } = props;

  // Whether to show the name infront of the component (false if used with a slider)
  const showName = props.showName !== undefined ? props.showName : true;

  const renderCount = useRef(0);
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');
  const id = getIdFromFullAccessPath(fullAccessPath);
  const webSettings = useContext(WebSettingsContext);
  let displayName = name;

  if (webSettings[fullAccessPath] && webSettings[fullAccessPath].displayName) {
    displayName = webSettings[fullAccessPath].displayName;
  }

  useEffect(() => {
    // emitting notification
    let notificationMsg = `${parentPath}.${name} changed to ${props.value}`;
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
        displayName={showName === true ? displayName : null}
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
