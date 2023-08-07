import React from 'react';
import { ButtonComponent } from './ButtonComponent';
import { NumberComponent } from './NumberComponent';
import { SliderComponent } from './SliderComponent';
import { EnumComponent } from './EnumComponent';
import { MethodComponent } from './MethodComponent';
import { AsyncMethodComponent } from './AsyncMethodComponent';
import { StringComponent } from './StringComponent';
import { ListComponent } from './ListComponent';
import { DataServiceComponent, DataServiceJSON } from './DataServiceComponent';

type AttributeType =
  | 'str'
  | 'bool'
  | 'float'
  | 'int'
  | 'Quantity'
  | 'list'
  | 'method'
  | 'DataService'
  | 'Enum'
  | 'NumberSlider';

type ValueType = boolean | string | number | object;
export interface Attribute {
  type: AttributeType;
  value?: ValueType | ValueType[];
  readonly: boolean;
  doc?: string | null;
  parameters?: Record<string, string>;
  async?: boolean;
  enum?: Record<string, string>;
}
type GenericComponentProps = {
  attribute: Attribute;
  name: string;
  parentPath: string;
  isInstantUpdate: boolean;
};

export const GenericComponent = React.memo(
  ({ attribute, name, parentPath, isInstantUpdate }: GenericComponentProps) => {
    if (attribute.type === 'bool') {
      return (
        <ButtonComponent
          name={name}
          parent_path={parentPath}
          docString={attribute.doc}
          readOnly={attribute.readonly}
          value={Boolean(attribute.value)}
        />
      );
    } else if (attribute.type === 'float' || attribute.type === 'int') {
      return (
        <NumberComponent
          name={name}
          type={attribute.type}
          parent_path={parentPath}
          docString={attribute.doc}
          readOnly={attribute.readonly}
          value={Number(attribute.value)}
          isInstantUpdate={isInstantUpdate}
        />
      );
    } else if (attribute.type === 'Quantity') {
      return (
        <NumberComponent
          name={name}
          type="float"
          parent_path={parentPath}
          docString={attribute.doc}
          readOnly={attribute.readonly}
          value={Number(attribute.value['magnitude'])}
          unit={attribute.value['unit']}
          isInstantUpdate={isInstantUpdate}
        />
      );
    } else if (attribute.type === 'NumberSlider') {
      return (
        <SliderComponent
          name={name}
          parent_path={parentPath}
          docString={attribute.doc}
          readOnly={attribute.readonly}
          value={attribute.value['value']['value']}
          min={attribute.value['min']['value']}
          max={attribute.value['max']['value']}
          stepSize={attribute.value['step_size']['value']}
          isInstantUpdate={isInstantUpdate}
        />
      );
    } else if (attribute.type === 'Enum') {
      return (
        <EnumComponent
          name={name}
          parent_path={parentPath}
          docString={attribute.doc}
          value={String(attribute.value)}
          enumDict={attribute.enum}
        />
      );
    } else if (attribute.type === 'method') {
      if (!attribute.async) {
        return (
          <MethodComponent
            name={name}
            parent_path={parentPath}
            docString={attribute.doc}
            parameters={attribute.parameters}
          />
        );
      } else {
        return (
          <AsyncMethodComponent
            name={name}
            parent_path={parentPath}
            docString={attribute.doc}
            parameters={attribute.parameters}
            value={attribute.value as Record<string, string>}
          />
        );
      }
    } else if (attribute.type === 'str') {
      return (
        <StringComponent
          name={name}
          value={attribute.value as string}
          readOnly={attribute.readonly}
          docString={attribute.doc}
          parent_path={parentPath}
          isInstantUpdate={isInstantUpdate}
        />
      );
    } else if (attribute.type === 'DataService') {
      return (
        <DataServiceComponent
          props={attribute.value as DataServiceJSON}
          parentPath={parentPath.concat('.', name)}
          isInstantUpdate={isInstantUpdate}
        />
      );
    } else if (attribute.type === 'list') {
      return (
        <ListComponent
          name={name}
          value={attribute.value as Attribute[]}
          docString={attribute.doc}
          parent_path={parentPath}
          isInstantUpdate={isInstantUpdate}
        />
      );
    } else {
      return <div key={name}>{name}</div>;
    }
  }
);
