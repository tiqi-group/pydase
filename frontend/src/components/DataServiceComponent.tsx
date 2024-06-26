import { useState } from 'react';
import React from 'react';
import { Card, Collapse } from 'react-bootstrap';
import { ChevronDown, ChevronRight } from 'react-bootstrap-icons';
import { SerializedValue, GenericComponent } from './GenericComponent';
import { LevelName } from './NotificationsComponent';

type DataServiceProps = {
  props: DataServiceJSON;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
};

export type DataServiceJSON = Record<string, SerializedValue>;

export const DataServiceComponent = React.memo(
  ({ props, isInstantUpdate, addNotification, displayName, id }: DataServiceProps) => {
    const [open, setOpen] = useState(true);

    if (displayName !== '') {
      return (
        <div className="component dataServiceComponent" id={id}>
          <Card>
            <Card.Header onClick={() => setOpen(!open)} style={{ cursor: 'pointer' }}>
              {displayName} {open ? <ChevronDown /> : <ChevronRight />}
            </Card.Header>
            <Collapse in={open}>
              <Card.Body>
                {Object.entries(props).map(([key, value]) => (
                  <GenericComponent
                    key={key}
                    attribute={value}
                    isInstantUpdate={isInstantUpdate}
                    addNotification={addNotification}
                  />
                ))}
              </Card.Body>
            </Collapse>
          </Card>
        </div>
      );
    } else {
      return (
        <div className="component dataServiceComponent" id={id}>
          {Object.entries(props).map(([key, value]) => (
            <GenericComponent
              key={key}
              attribute={value}
              isInstantUpdate={isInstantUpdate}
              addNotification={addNotification}
            />
          ))}
        </div>
      );
    }
  }
);
