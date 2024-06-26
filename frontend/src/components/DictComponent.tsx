import React, { useEffect, useRef } from 'react';
import { DocStringComponent } from './DocStringComponent';
import { SerializedValue, GenericComponent } from './GenericComponent';
import { LevelName } from './NotificationsComponent';

type DictComponentProps = {
  value: Record<string, SerializedValue>;
  docString: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  id: string;
};

export const DictComponent = React.memo((props: DictComponentProps) => {
  const { value, docString, isInstantUpdate, addNotification, id } = props;

  const renderCount = useRef(0);
  const valueArray = Object.values(value);

  useEffect(() => {
    renderCount.current++;
  }, [props]);

  return (
    <div className={'listComponent'} id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
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
