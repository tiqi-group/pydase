import React from "react";
import { DocStringComponent } from "./DocStringComponent";
import { GenericComponent } from "./GenericComponent";
import { LevelName } from "./NotificationsComponent";
import { SerializedObject } from "../types/SerializedObject";
import { useRenderCount } from "../hooks/useRenderCount";

interface DictComponentProps {
  value: Record<string, SerializedObject>;
  docString: string | null;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  id: string;
}

export const DictComponent = React.memo((props: DictComponentProps) => {
  const { value, docString, isInstantUpdate, addNotification, id } = props;

  const renderCount = useRenderCount();
  const valueArray = Object.values(value);

  return (
    <div className={"listComponent"} id={id}>
      {process.env.NODE_ENV === "development" && <div>Render count: {renderCount}</div>}
      <DocStringComponent docString={docString} />
      {valueArray.map((item) => {
        return (
          <GenericComponent
            key={item.full_access_path}
            attribute={item}
            isInstantUpdate={isInstantUpdate}
            addNotification={addNotification}
          />
        );
      })}
    </div>
  );
});

DictComponent.displayName = "DictComponent";
