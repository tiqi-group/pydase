import React from 'react';
import { LevelName } from './NotificationsComponent';
import { DataServiceComponent, DataServiceJSON } from './DataServiceComponent';
import { MethodComponent } from './MethodComponent';

type DeviceConnectionProps = {
  name: string;
  props: DataServiceJSON;
  parentPath: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
};

export const DeviceConnectionComponent = React.memo(
  ({
    name,
    props,
    parentPath,
    isInstantUpdate,
    addNotification,
    displayName,
    id
  }: DeviceConnectionProps) => {
    const { connected, connect, ...updatedProps } = props;
    const connectedVal = connected.value;

    const fullAccessPath = [parentPath, name].filter((element) => element).join('.');

    return (
      <div className="deviceConnectionComponent" id={id}>
        {!connectedVal && (
          <div className="overlayContent">
            <div>
              {displayName != '' ? displayName : 'Device'} is currently not available!
            </div>
            <MethodComponent
              name="connect"
              parentPath={fullAccessPath}
              parameters={connect.parameters}
              docString={connect.doc}
              addNotification={addNotification}
              displayName={'reconnect'}
              id={id + '-connect'}
            />
          </div>
        )}
        <DataServiceComponent
          name={name}
          props={updatedProps}
          parentPath={parentPath}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          displayName={displayName}
          id={id}
        />
      </div>
    );
  }
);
