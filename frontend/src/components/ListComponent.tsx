import React, { useEffect, useRef } from 'react';
import { DocStringComponent } from './DocStringComponent';
import { Attribute, GenericComponent } from './GenericComponent';

interface ListComponentProps {
  name: string;
  parentPath?: string;
  value: Attribute[];
  docString: string;
  isInstantUpdate: boolean;
  addNotification: (string) => void;
}

export const ListComponent = React.memo((props: ListComponentProps) => {
  const { name, parentPath, value, docString, isInstantUpdate, addNotification } =
    props;

  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  }, [props]);

  return (
    <div className={'listComponent'} id={parentPath.concat(name)}>
      {process.env.NODE_ENV === 'development' && (
        <p>Render count: {renderCount.current}</p>
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
