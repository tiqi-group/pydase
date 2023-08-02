import React, { MouseEventHandler, useEffect, useRef, useState } from 'react';
import { OverlayTrigger, Badge, Button, Tooltip, ToggleButton } from 'react-bootstrap';

interface ButtonComponentProps {
  name: string;
  fullname?: string;
  value: boolean;
  readOnly: boolean;
  docString: string;
  onToggle?: MouseEventHandler;
  mapping?: [string, string]; // Enforce a tuple of two strings
}

export const ButtonComponent = React.memo((props: ButtonComponentProps) => {
  const renderCount = useRef(0);

  const [checked, setChecked] = useState(false);

  useEffect(() => {
    renderCount.current++;
  });
  const { name, fullname, value, readOnly, docString, onToggle, mapping } = props;

  const buttonName = mapping ? (value ? mapping[0] : mapping[1]) : name;

  const tooltip = <Tooltip id="tooltip">{docString}</Tooltip>;

  return (
    <div className={'component boolean'} id={fullname}>
      <p>Render count: {renderCount.current}</p>
      <ToggleButton
        id="toggle-check"
        type="checkbox"
        // variant="secondary"
        variant={checked ? 'success' : 'secondary'}
        checked={checked}
        value={fullname}
        onMouseUp={onToggle}
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
