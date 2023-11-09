import React, { useEffect, useRef } from 'react';
import { ToggleButton } from 'react-bootstrap';
import { setAttribute } from '../socket';
import { DocStringComponent } from './DocStringComponent';
import { getIdFromFullAccessPath } from '../utils/stringUtils';

interface ButtonComponentProps {
  name: string;
  parentPath?: string;
  value: boolean;
  readOnly: boolean;
  docString: string;
  mapping?: [string, string]; // Enforce a tuple of two strings
  addNotification: (message: string) => void;
}

export const ButtonComponent = React.memo((props: ButtonComponentProps) => {
  const { name, parentPath, value, readOnly, docString, mapping, addNotification } =
    props;
  const buttonName = mapping ? (value ? mapping[0] : mapping[1]) : name;
  const id = getIdFromFullAccessPath(parentPath.concat('.' + name));

  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });

  useEffect(() => {
    addNotification(`${parentPath}.${name} changed to ${value}.`);
  }, [props.value]);

  const setChecked = (checked: boolean) => {
    setAttribute(name, parentPath, checked);
  };

  return (
    <div className={'buttonComponent'} id={id}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}

      <DocStringComponent docString={docString} />
      <ToggleButton
        id={`toggle-check-${id}`}
        type="checkbox"
        variant={value ? 'success' : 'secondary'}
        checked={value}
        value={parentPath}
        disabled={readOnly}
        onChange={(e) => setChecked(e.currentTarget.checked)}>
        <p>{buttonName}</p>
      </ToggleButton>
    </div>
  );
});
