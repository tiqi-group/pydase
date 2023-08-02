import React, { useEffect, useRef } from 'react';
import { DocStringComponent } from './DocStringComponent';
import { Attribute, GenericComponent } from './GenericComponent';

interface ListComponentProps {
  name: string;
  parent_path?: string;
  value: Attribute[];
  docString: string;
  isInstantUpdate: boolean;
}

export const ListComponent = React.memo((props: ListComponentProps) => {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });

  const { name, parent_path, value, docString, isInstantUpdate } = props;

  return (
    <div className={'listComponent'} id={parent_path.concat(name)}>
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
            parentPath={parent_path}
            isInstantUpdate={isInstantUpdate}
          />
        );
      })}
    </div>
  );
});
