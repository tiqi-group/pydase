import React from 'react';

interface ComponentProps {
  name: string;
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

export const Component = ({
  name,
  value,
  readOnly,
  type,
  docString
}: ComponentProps) => {
  switch (type) {
    case 'int':
    case 'float':
      return (
        <input
          type="number"
          name={name}
          value={value}
          readOnly={readOnly}
          title={docString}
        />
      );
    case 'str':
      return (
        <input
          type="text"
          name={name}
          value={value}
          readOnly={readOnly}
          title={docString}
        />
      );
    case 'bool':
      return (
        <input
          type="checkbox"
          name={name}
          checked={value}
          disabled={readOnly}
          title={docString}
        />
      );
    case 'method':
      return <p>Method: {name}</p>;
    default:
      return <p>Unsupported type: {type}</p>;
  }
};
