import React, { useEffect, useRef } from 'react';
import { ToggleButton } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
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
  displayName: string;
  id: string;
};

export const ButtonComponent = React.memo((props: ButtonComponentProps) => {
  const {
    value,
    readOnly,
    docString,
    addNotification,
    changeCallback = () => {},
    displayName,
    id
  } = props;
  // const buttonName = props.mapping ? (value ? props.mapping[0] : props.mapping[1]) : name;
  const fullAccessPath = [props.parentPath, props.name]
    .filter((element) => element)
    .join('.');

  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${fullAccessPath} changed to ${value}.`);
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
        value={displayName}
        disabled={readOnly}
        onChange={(e) => setChecked(e.currentTarget.checked)}>
        {displayName}
        <DocStringComponent docString={docString} />
      </ToggleButton>
    </div>
  );
});
