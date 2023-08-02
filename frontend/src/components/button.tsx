import React, { MouseEventHandler } from 'react';
import { OverlayTrigger, Badge, Button, Tooltip } from 'react-bootstrap';

interface ButtonComponentProps {
  name: string;
  fullname?: string;
  value: boolean;
  readOnly: boolean;
  docString: string;
  onToggle?: MouseEventHandler;
  mapping?: [string, string]; // Enforce a tuple of two strings
}

const ButtonComponentRef = React.forwardRef<HTMLDivElement, ButtonComponentProps>(
  (props, ref) => {
    const { name, fullname, value, readOnly, docString, onToggle, mapping } = props;

    const buttonName = mapping ? (value ? mapping[0] : mapping[1]) : name;

    const tooltip = <Tooltip id="tooltip">{docString}</Tooltip>;

    return (
      <div className={'component boolean'} id={fullname} ref={ref}>
        <Button
          type={'button'}
          variant={value ? 'success' : 'secondary'}
          onMouseUp={onToggle}
          disabled={readOnly}>
          <p>{buttonName}</p>
        </Button>

        {docString && (
          <OverlayTrigger placement="bottom" overlay={tooltip}>
            <Badge pill className="tooltip-trigger" bg="light" text="dark">
              ?
            </Badge>
          </OverlayTrigger>
        )}
      </div>
    );
  }
);

export const ButtonComponent = React.memo(ButtonComponentRef);
