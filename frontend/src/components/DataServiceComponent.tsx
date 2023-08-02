import { useState } from 'react';
import { ButtonComponent } from './ButtonComponent';
import { NumberComponent } from './NumberComponent';
import { SliderComponent } from './SliderComponent';
import { EnumComponent } from './EnumComponent';
import { MethodComponent } from './MethodComponent';
import { AsyncMethodComponent } from './AsyncMethodComponent';
import React from 'react';
import { Card, Collapse } from 'react-bootstrap';
import { ChevronDown, ChevronRight } from 'react-bootstrap-icons';
import { StringComponent } from './StringComponent';

type AttributeType =
  | 'str'
  | 'bool'
  | 'float'
  | 'int'
  | 'method'
  | 'DataService'
  | 'Enum'
  | 'NumberSlider';

type ValueType = boolean | string | number | object;
interface Attribute {
  type: AttributeType;
  value?: ValueType;
  readonly: boolean;
  doc?: string | null;
  parameters?: Record<string, string>;
  async?: boolean;
  enum?: Record<string, string>;
}
type DataServiceProps = {
  props: DataServiceJSON;
  parentPath?: string;
};

export type DataServiceJSON = Record<string, Attribute>;

export const DataServiceComponent = React.memo(
  ({ props, parentPath = 'DataService' }: DataServiceProps) => {
    const [open, setOpen] = useState(true);

    return (
      <div className="App">
        <Card className="mb-3">
          <Card.Header
            onClick={() => setOpen(!open)}
            style={{ cursor: 'pointer' }} // Change cursor style on hover
          >
            {parentPath} {open ? <ChevronDown /> : <ChevronRight />}
          </Card.Header>
          <Collapse in={open}>
            <Card.Body>
              {Object.entries(props).map(([key, value]) => {
                if (value.type === 'bool') {
                  return (
                    <div key={key}>
                      <ButtonComponent
                        name={key}
                        parent_path={parentPath}
                        docString={value.doc}
                        readOnly={value.readonly}
                        value={Boolean(value.value)}
                      />
                    </div>
                  );
                } else if (value.type === 'float' || value.type === 'int') {
                  return (
                    <div key={key}>
                      <NumberComponent
                        name={key}
                        type={value.type}
                        parent_path={parentPath}
                        docString={value.doc}
                        readOnly={value.readonly}
                        value={Number(value.value)}
                      />
                    </div>
                  );
                } else if (value.type === 'NumberSlider') {
                  return (
                    <div key={key}>
                      <SliderComponent
                        name={key}
                        parent_path={parentPath}
                        docString={value.doc}
                        readOnly={value.readonly}
                        value={value.value['value']['value']}
                        min={value.value['min']['value']}
                        max={value.value['max']['value']}
                        stepSize={value.value['step_size']['value']}
                      />
                    </div>
                  );
                } else if (value.type === 'Enum') {
                  return (
                    <div key={key}>
                      <EnumComponent
                        name={key}
                        parent_path={parentPath}
                        docString={value.doc}
                        value={String(value.value)}
                        enumDict={value.enum}
                      />
                    </div>
                  );
                } else if (value.type === 'method') {
                  if (!value.async) {
                    return (
                      <div key={key}>
                        <MethodComponent
                          name={key}
                          parent_path={parentPath}
                          docString={value.doc}
                          parameters={value.parameters}
                        />
                      </div>
                    );
                  } else {
                    return (
                      <div key={key}>
                        <AsyncMethodComponent
                          name={key}
                          parent_path={parentPath}
                          docString={value.doc}
                          parameters={value.parameters}
                          value={value.value as Record<string, string>}
                        />
                      </div>
                    );
                  }
                } else if (value.type === 'str') {
                  return (
                    <div key={key}>
                      <StringComponent
                        name={key}
                        value={value.value as string}
                        readOnly={value.readonly}
                        docString={value.doc}
                        parent_path={parentPath}
                      />
                    </div>
                  );
                } else if (value.type === 'DataService') {
                  return (
                    <div key={key}>
                      <DataServiceComponent
                        props={value.value as DataServiceJSON}
                        parentPath={parentPath.concat('.', key)}
                      />
                    </div>
                  );
                } else {
                  return <div key={key}></div>;
                }
              })}
            </Card.Body>
          </Collapse>
        </Card>
      </div>
    );
  }
);
