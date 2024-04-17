import React, { useEffect, useRef } from 'react';
import { ToggleButton } from 'react-bootstrap';
import { DocStringComponent } from './DocStringComponent';
import { SerializedValue } from './GenericComponent';
import { LevelName } from './NotificationsComponent';

type ButtonComponentProps = {
  fullAccessPath: string;
  value: boolean;
  readOnly: boolean;
  docString: string;
  mapping?: [string, string]; // Enforce a tuple of two strings
  addNotification: (message: string, levelname?: LevelName) => void;
  changeCallback?: (value: SerializedValue, callback?: (ack: unknown) => void) => void;
  displayName: string;
  id: string;
};

export const ButtonComponent = React.memo((props: ButtonComponentProps) => {
  const {
    value,
    fullAccessPath,
    readOnly,
    docString,
    addNotification,
    changeCallback = () => {},
    displayName,
    id
  } = props;
  // const buttonName = props.mapping ? (value ? props.mapping[0] : props.mapping[1]) : name;

  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${fullAccessPath} changed to ${value}.`);
  }, [props.value]);

  const setChecked = (checked: boolean) => {
    changeCallback({
      type: 'bool',
      value: checked,
      full_access_path: fullAccessPath,
      readonly: readOnly,
      doc: docString
    });
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
