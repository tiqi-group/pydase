import React, { useEffect, useRef } from 'react';
import { DocStringComponent } from './DocStringComponent';
import { Attribute, GenericComponent } from './GenericComponent';
import { getIdFromFullAccessPath } from '../utils/stringUtils';
import { LevelName } from './NotificationsComponent';

interface ListComponentProps {
  name: string;
  parentPath?: string;
  value: Attribute[];
  docString: string;
  isInstantUpdate: boolean;
  addNotification: (message: string, levelname?: LevelName) => void;
}

export const ListComponent = React.memo((props: ListComponentProps) => {
  const { name, parentPath, value, docString, isInstantUpdate, addNotification } =
    props;

  const renderCount = useRef(0);
  const fullAccessPath = [parentPath, name].filter((element) => element).join('.');
  const id = getIdFromFullAccessPath(fullAccessPath);

  useEffect(() => {
    renderCount.current++;
  }, [props]);

  return (
    <div className={'listComponent'} id={id}>
      {process.env.NODE_ENV === 'development' && (
        <div>Render count: {renderCount.current}</div>
      )}
      <DocStringComponent docString={docString} />
      {value.map((item, index) => {
        return (
          <GenericComponent
            key={`${name}[${index}]`}
            attribute={item}
            name={`${name}[${index}]`}
            parentPath={parentPath}
            isInstantUpdate={isInstantUpdate}
            addNotification={addNotification}
          />
        );
      })}
    </div>
  );
});
