import React from "react";
import { LevelName } from "./NotificationsComponent";
import { DataServiceComponent, DataServiceJSON } from "./DataServiceComponent";
import { MethodComponent } from "./MethodComponent";

interface DeviceConnectionProps {
  fullAccessPath: string;
  props: DataServiceJSON;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  displayName: string;
  id: string;
}

export const DeviceConnectionComponent = React.memo(
  ({
    fullAccessPath,
    props,
    isInstantUpdate,
    addNotification,
    displayName,
    id,
  }: DeviceConnectionProps) => {
    const { connected, connect, ...updatedProps } = props;
    const connectedVal = connected.value;

    return (
      <div className="deviceConnectionComponent" id={id}>
        {!connectedVal && (
          <div className="overlayContent">
            <div>
              {displayName != "" ? displayName : "Device"} is currently not available!
            </div>
            <MethodComponent
              fullAccessPath={`${fullAccessPath}.connect`}
              docString={connect.doc}
              addNotification={addNotification}
              displayName={"reconnect"}
              id={id + "-connect"}
              render={true}
            />
          </div>
        )}
        <DataServiceComponent
          props={updatedProps}
          isInstantUpdate={isInstantUpdate}
          addNotification={addNotification}
          displayName={displayName}
          id={id}
        />
      </div>
    );
  },
);

DeviceConnectionComponent.displayName = "DeviceConnectionComponent";
