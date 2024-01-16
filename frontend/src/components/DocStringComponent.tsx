import { Badge, Tooltip, OverlayTrigger } from 'react-bootstrap';
import React from 'react';

type DocStringProps = {
  docString?: string;
};

export const DocStringComponent = React.memo((props: DocStringProps) => {
  const { docString } = props;
  if (!docString) {
    return null; // render nothing if docString is not provided
  }

  const tooltip = <Tooltip id="tooltip">{docString}</Tooltip>;

  return (
    <OverlayTrigger placement="bottom" overlay={tooltip}>
      <Badge pill className="tooltip-trigger" bg="light" text="dark">
        ?
      </Badge>
    </OverlayTrigger>
  );
});
