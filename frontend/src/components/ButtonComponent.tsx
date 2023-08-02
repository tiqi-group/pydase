import React, { useEffect, useRef } from 'react';
import { OverlayTrigger, Badge, Tooltip, ToggleButton } from 'react-bootstrap';
import { socket } from '../socket';

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
  const { name, parent_path: fullname, value, readOnly, docString, mapping } = props;

  const buttonName = mapping ? (value ? mapping[0] : mapping[1]) : name;

  const tooltip = <Tooltip id="tooltip">{docString}</Tooltip>;

  const setChecked = (checked: boolean) => {
    socket.emit('frontend_update', {
      name: name,
      fullname: fullname,
      value: checked
    });
  };

  return (
    <div className={'component boolean'} id={fullname}>
      <p>Render count: {renderCount.current}</p>
      <ToggleButton
        id="toggle-check"
        type="checkbox"
        variant={value ? 'success' : 'secondary'}
        checked={value}
        value={fullname}
        disabled={readOnly}
        onChange={(e) => setChecked(e.currentTarget.checked)}>
        <p>{buttonName}</p>
      </ToggleButton>

      {docString && (
        <OverlayTrigger placement="bottom" overlay={tooltip}>
          <Badge pill className="tooltip-trigger" bg="light" text="dark">
            ?
          </Badge>
        </OverlayTrigger>
      )}
    </div>
  );
});
