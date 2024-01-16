import { useContext } from 'react';
import React from 'react';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { LevelName } from './NotificationsComponent';
import { WebSettingsContext } from '../WebSettings';
import { DataServiceComponent, DataServiceJSON } from './DataServiceComponent';
import { MethodComponent } from './MethodComponent';

type DeviceConnectionProps = {
  name: string;
  props: DataServiceJSON;
  parentPath: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
};

export const DeviceConnectionComponent = React.memo(
  ({
    name,
    props,
    parentPath,
    isInstantUpdate,
    addNotification
  }: DeviceConnectionProps) => {
    const { available, connect, ...updatedProps } = props;
    const availableVal = available.value;

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
      <div className="deviceConnectionComponent" id={id}>
        {!availableVal && (
          <div className="overlayContent">
            <div>{displayName} is currently not available!</div>
            <MethodComponent
              name="connect"
              parentPath={fullAccessPath}
              parameters={connect.parameters}
              docString={connect.doc}
              addNotification={addNotification}
            />
          </div>
        )}
        <DataServiceComponent
          name={name}
          props={updatedProps}
          parentPath={parentPath}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
        />
      </div>
    );
  }
);
