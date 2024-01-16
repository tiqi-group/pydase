import { useContext, useState } from 'react';
import React from 'react';
import { Card, Collapse } from 'react-bootstrap';
import { ChevronDown, ChevronRight } from 'react-bootstrap-icons';
import { Attribute, GenericComponent } from './GenericComponent';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { LevelName } from './NotificationsComponent';
import { WebSettingsContext } from '../WebSettings';

type DataServiceProps = {
  name: string;
  props: DataServiceJSON;
  parentPath?: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
};

export type DataServiceJSON = Record<string, Attribute>;

export const DataServiceComponent = React.memo(
  ({
    name,
    props,
    parentPath = '',
    isInstantUpdate,
    addNotification
  }: DataServiceProps) => {
    const [open, setOpen] = useState(true);
    let fullAccessPath = parentPath;
    if (name) {
      fullAccessPath = [parentPath, name].filter((element) => element).join('.');
    }
    const id = getIdFromFullAccessPath(fullAccessPath);

    const webSettings = useContext(WebSettingsContext);
    let displayName = fullAccessPath;

    if (webSettings[fullAccessPath] && webSettings[fullAccessPath].displayName) {
      displayName = webSettings[fullAccessPath].displayName;
    }

    return (
      <div className="component dataServiceComponent" id={id}>
        <Card>
          <Card.Header
            onClick={() => setOpen(!open)}
            style={{ cursor: 'pointer' }} // Change cursor style on hover
          >
            {displayName} {open ? <ChevronDown /> : <ChevronRight />}
          </Card.Header>
          <Collapse in={open}>
            <Card.Body>
              {Object.entries(props).map(([key, value]) => {
                return (
                  <GenericComponent
                    key={key}
                    attribute={value}
                    name={key}
                    parentPath={fullAccessPath}
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
