import React, { useEffect, useRef } from 'react';
import { DocStringComponent } from './DocStringComponent';
import { SerializedValue, GenericComponent } from './GenericComponent';
import { LevelName } from './NotificationsComponent';

type ListComponentProps = {
  value: SerializedValue[];
  docString: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
  id: string;
};

export const ListComponent = React.memo((props: ListComponentProps) => {
  const { value, docString, isInstantUpdate, addNotification, id } = props;

  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  }, [props]);

  return (
    <div className={'listComponent'} id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <DocStringComponent docString={docString} />
      {value.map((item) => {
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
