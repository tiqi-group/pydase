import React, { useEffect, useState } from 'react';
import { Component, ComponentLabel } from './components/component';
import { ButtonComponent } from './components/button';
import { socket } from './socket';

type AttributeType = 'str' | 'bool' | 'float' | 'int' | 'method' | 'Subclass';

interface Attribute {
  type: AttributeType;
  value?: any;
  readonly: boolean;
  doc?: string | null;
  parameters?: Record<string, string>;
  async?: boolean;
}

type MyData = Record<string, Attribute>;

const App = () => {
  const [data, setData] = useState<MyData | null>(null);
  const [isConnected, setIsConnected] = useState(socket.connected);

  useEffect(() => {
    // Fetch data from the API when the component mounts
    fetch('http://localhost:8001/service-properties')
      .then((response) => response.json())
      .then(setData);
    function onConnect() {
      setIsConnected(true);
    }

    function onDisconnect() {
      setIsConnected(false);
    }

    function onNotify(value: Record<string, any>) {
      console.log(value);
    }

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('notify', onNotify);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('notify', onNotify);
    };
  }, []);

  // While the data is loading
  if (!data) {
    return <p>Loading...</p>;
  }
  return (
    <div className="App">
      {Object.entries(data).map(([key, value]) => {
        if (value.type === 'bool') {
          return (
            <div key={key}>
              <ButtonComponent
                name={key}
                docString={value.doc}
                readOnly={value.readonly}
                value={value.value}
              />
            </div>
          );
        } else if (!value.async) {
          return (
            <div key={key}>
              <ComponentLabel name={key} docString={value.doc} />
              <Component
                name={key}
                value={value.value}
                readOnly={value.readonly}
                type={value.type}
                docString={value.doc}
              />
            </div>
          );
        } else {
          return <div key={key}></div>;
        }
      })}
    </div>
  );
};

export default App;
