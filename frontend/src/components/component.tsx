import React, { useEffect, useRef } from 'react';

interface ComponentProps {
  name: string;
  parent_path: string;
  value: any;
  readOnly: boolean;
  type: string;
  docString: string;
}

export const ComponentLabel = ({
  name,
  docString
}: {
  name: string;
  docString: string;
}) => {
  return <label title={docString}>{name}</label>;
};

export const Component = React.memo(
  ({ name, parent_path, value, readOnly, type, docString }: ComponentProps) => {
    const renderCount = useRef(0);

    useEffect(() => {
      renderCount.current++;
    });
    switch (type) {
      case 'str':
        return (
          <>
            <p>Render count: {renderCount.current}</p>
            <input
              type="text"
              name={name}
              value={value}
              readOnly={readOnly}
              title={docString}
              id={parent_path}
            />
          </>
        );
      case 'method':
        return (
          <>
            <p>Render count: {renderCount.current}</p>
            <p>Method: {name}</p>
          </>
        );
      default:
        return <p>Unsupported type: {type}</p>;
    }
  }
);
