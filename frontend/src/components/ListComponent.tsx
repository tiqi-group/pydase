import React, { useEffect, useRef } from 'react';
import { DocStringComponent } from './DocStringComponent';
import { GenericComponent } from './GenericComponent';

interface ListComponentProps {
  name: string;
  parent_path?: string;
  value: object[];
  docString: string;
}

export const ListComponent = React.memo((props: ListComponentProps) => {
  const renderCount = useRef(0);

  useEffect(() => {
    renderCount.current++;
  });

  const { name, parent_path, value, docString } = props;

  return (
    <div className={'component boolean'} id={parent_path.concat(name)}>
      <p>Render count: {renderCount.current}</p>
      <DocStringComponent docString={docString} />
      {value.map((item, index) => {
        return (
          <GenericComponent
            key={`${name}[${index}]`}
            attribute={item}
            name={`${name}[${index}]`}
            parentPath={parent_path}
          />
        );
      })}
    </div>
  );
});
