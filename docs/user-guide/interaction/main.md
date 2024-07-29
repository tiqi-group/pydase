# Interacting with `pydase` Services

`pydase` offers multiple ways for users to interact with the services they create, providing flexibility and convenience for different use cases. This section outlines the primary interaction methods available, including an auto-generated frontend, a RESTful API, and a Python client based on Socket.IO.

{%
   include-markdown "./Auto-generated Frontend.md"
   heading-offset=1
%}

{%
   include-markdown "./RESTful API.md"
   heading-offset=1
%}

{%
   include-markdown "./Python Client.md"
   heading-offset=1
%}

<!-- ## 2. **Socket.IO for Real-Time Updates** -->
<!-- For scenarios requiring real-time data updates, `pydase` includes a Socket.IO server. This feature is ideal for applications where live data tracking is crucial, such as monitoring systems or interactive dashboards. -->
<!---->
<!-- ### Key Features: -->
<!-- - **Live Data Streams**: Receive real-time updates for data changes. -->
<!-- - **Event-Driven Communication**: Utilize event-based messaging to push updates and handle client actions. -->
<!---->
<!-- ### Example Usage: -->
<!-- Clients can connect to the Socket.IO server to receive updates: -->
<!-- ```javascript -->
<!-- var socket = io.connect('http://<hostname>:<port>'); -->
<!-- socket.on('<event_name>', function(data) { -->
<!--     console.log(data); -->
<!-- }); -->
<!-- ``` -->
<!---->
<!-- **Use Cases:** -->
<!---->
<!-- - Real-time monitoring and alerts -->
<!-- - Live data visualization -->
<!-- - Collaborative applications -->
<!---->
<!-- ## 3. **Auto-Generated Frontend** -->
<!-- `pydase` automatically generates a web frontend based on the service definitions. This frontend is a convenient interface for interacting with the service, especially for users who prefer a graphical interface over command-line or code-based interactions. -->
<!---->
<!-- ### Key Features: -->
<!-- - **User-Friendly Interface**: Intuitive and easy to use, with real-time interaction capabilities. -->
<!-- - **Customizable**: Adjust the frontend's appearance and functionality to suit specific needs. -->
<!---->
<!-- ### Accessing the Frontend: -->
<!-- Once the service is running, access the frontend via a web browser: -->
<!-- ``` -->
<!-- http://<hostname>:<port> -->
<!-- ``` -->
<!---->
<!-- **Use Cases:** -->
<!---->
<!-- - End-user interfaces for data control and visualization -->
<!-- - Rapid prototyping and testing -->
<!-- - Demonstrations and training -->
<!---->
<!-- ## 4. **Python Client** -->
<!-- `pydase` also provides a Python client for programmatic interactions. This client is particularly useful for developers who want to integrate `pydase` services into other Python applications or automate interactions. -->
<!---->
<!-- ### Key Features: -->
<!-- - **Direct Interaction**: Call methods and access properties as if they were local. -->
<!-- - **Tab Completion**: Supports tab completion in interactive environments like Jupyter notebooks. -->
<!---->
<!-- ### Example Usage: -->
<!-- ```python -->
<!-- import pydase -->
<!---->
<!-- client = pydase.Client(hostname="<ip_addr>", port=8001) -->
<!-- service = client.proxy -->
<!-- service.some_method() -->
<!-- ``` -->
<!---->
<!-- **Use Cases:** -->
<!---->
<!-- - Integrating with other Python applications -->
<!-- - Automation and scripting -->
<!-- - Data analysis and manipulation -->
