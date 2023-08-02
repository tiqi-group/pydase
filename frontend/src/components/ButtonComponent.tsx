import React, { useEffect, useRef } from 'react';
import { ToggleButton } from 'react-bootstrap';
import { emit_update } from '../socket';
import { DocStringComponent } from './DocStringComponent';

interface ButtonComponentProps {
  name: string;
  parent_path?: string;
  value: boolean;
  readOnly: boolean;
  docString: string;
  mapping?: [string, string]; // Enforce a tuple of two strings
}

export const ButtonComponent = React.memo((props: ButtonComponentProps) => {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });
  const { name, parent_path, value, readOnly, docString, mapping } = props;

  const buttonName = mapping ? (value ? mapping[0] : mapping[1]) : name;

  const setChecked = (checked: boolean) => {
    emit_update(name, parent_path, checked);
  };

  return (
    <div className={'buttonComponent'} id={parent_path.concat('.' + name)}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
      )}

      <DocStringComponent docString={docString} />
      <ToggleButton
        id={`toggle-check-${parent_path}.${name}`}
        type="checkbox"
        variant={value ? 'success' : 'secondary'}
        checked={value}
        value={parent_path}
        disabled={readOnly}
        onChange={(e) => setChecked(e.currentTarget.checked)}>
        <p>{buttonName}</p>
      </ToggleButton>
    </div>
  );
});
