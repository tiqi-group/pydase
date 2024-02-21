import React, { useContext, useEffect, useRef } from 'react';
import { WebSettingsContext } from '../WebSettings';
import { ToggleButton } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { LevelName } from './NotificationsComponent';

type ButtonComponentProps = {
  name: string;
  parentPath?: string;
  value: boolean;
  readOnly: boolean;
  docString: string;
  mapping?: [string, string]; // Enforce a tuple of two strings
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (
    value: unknown,
    attributeName?: string,
    prefix?: string,
    callback?: (ack: unknown) => void
  ) => void;
};

export const ButtonComponent = React.memo((props: ButtonComponentProps) => {
  const {
    name,
    parentPath,
    value,
    readOnly,
    docString,
    addNotification,
    changeCallback = () => {}
  } = props;
  // const buttonName = props.mapping ? (value ? props.mapping[0] : props.mapping[1]) : name;
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');
  const id = getIdFromFullAccessPath(fullAccessPath);
  const webSettings = useContext(WebSettingsContext);
  let displayName = name;

  if (webSettings[fullAccessPath] && webSettings[fullAccessPath].displayName) {
    displayName = webSettings[fullAccessPath].displayName;
  }

  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${parentPath}.${name} changed to ${value}.`);
  }, [props.value]);

  const setChecked = (checked: boolean) => {
    changeCallback(checked);
  };

  return (
    <div className={'component buttonComponent'} id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}

      <ToggleButton
        id={`toggle-check-${id}`}
        type="checkbox"
        variant={value ? 'success' : 'secondary'}
        checked={value}
        value={parentPath}
        disabled={readOnly}
        onChange={(e) => setChecked(e.currentTarget.checked)}>
        {displayName}
        <DocStringComponent docString={docString} />
      </ToggleButton>
    </div>
  );
});
