import { useState } from 'react';
import React from 'react';
import { Card, Collapse } from 'react-bootstrap';
import { ChevronDown, ChevronRight } from 'react-bootstrap-icons';
import { Attribute, GenericComponent } from './GenericComponent';

type DataServiceProps = {
  props: DataServiceJSON;
  parentPath?: string;
  isInstantUpdate: boolean;
  addNotification: (message: string) => void;
};

export type DataServiceJSON = Record<string, Attribute>;

export const DataServiceComponent = React.memo(
  ({
    props,
    parentPath = 'DataService',
    isInstantUpdate,
    addNotification
  }: DataServiceProps) => {
    const [open, setOpen] = useState(true);

    return (
      <div className="dataServiceComponent">
        <Card className="mb-3">
          <Card.Header
            onClick={() => setOpen(!open)}
            style={{ cursor: 'pointer' }} // Change cursor style on hover
          >
            {parentPath} {open ? <ChevronDown /> : <ChevronRight />}
          </Card.Header>
          <Collapse in={open}>
            <Card.Body>
              {Object.entries(props).map(([key, value]) => {
                return (
                  <GenericComponent
                    key={key}
                    attribute={value}
                    name={key}
                    parentPath={parentPath}
                    isInstantUpdate={isInstantUpdate}
                    addNotification={addNotification}
                  />
                );
              })}
            </Card.Body>
          </Collapse>
        </Card>
      </div>
    );
  }
);
