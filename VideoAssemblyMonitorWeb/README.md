# Video Assembly Monitor Web （Frontend）

This is the frontend part of the **Video Assembly Monitor** project. It is built using **Vite**, **React**, **TypeScript**, and **Ant Design** to provide a responsive, user-friendly interface for monitoring and interacting with the assembly process.

## REST API Documentation

For the backend API, a detailed REST API documentation is available. This includes all available endpoints, their parameters, and responses.

- [REST API Documentation on Postman](https://www.postman.com/satellite-astronaut-90149468/my-workspace/collection/l4oh81m/api-documentation?action=share&creator=42644368)

## Project Overview

The **Video Assembly Monitor** project is designed to help monitor and track assembly processes using advanced computer vision techniques like **hand tracking** and **object detection**. This system provides real-time feedback for assembly verification and improvement by analyzing video feeds from assembly lines or workshops. The system consists of a **backend** built with **Spring Boot** and a **frontend** built with **Vite**, **React**, **TypeScript**, and **Ant Design**.

### Core Features
- **Hand Tracking**: The project utilizes **MediaPipe** for detecting and tracking the user's hand gestures during the assembly process. This allows the system to recognize gestures such as grabbing and placing parts.
- **Object Detection**: **YOLO (You Only Look Once)** is employed to detect and identify objects (such as parts and tools) involved in the assembly process.
- **Real-time Monitoring**: The system provides real-time updates and feedback based on the visual analysis of assembly steps.
- **Progress Tracking**: Visual progress tracking for assembly tasks, showing a step-by-step guide and the current state (e.g., in progress, completed).
- **Interactive Interface**: The frontend offers a user-friendly interface to visualize assembly progress, monitor the status of various parts, and interact with the system for efficient management.

### Backend

The backend is available in a separate repository, which can be found [here](https://github.com/LtSeed/VideoAssemblyMonitor). 
## Frontend Technology Stack

The frontend utilizes the following dependencies:

### Core Dependencies:
- **@ant-design/charts**: A charting library from Ant Design for creating rich and interactive data visualizations.
- **Ant Design (antd)**: A popular UI component library providing high-quality components for building modern user interfaces.
- **Axios**: A promise-based HTTP client for making API requests to the backend.
- **Lodash**: A utility library for working with arrays, numbers, objects, strings, etc.
- **React**: The core library for building the user interface with a component-based architecture.
- **React-DOM**: Provides the DOM-specific methods for React.
- **React Google Charts**: A React wrapper for integrating Google Charts into the application for visualizing data.
- **React Router**: A library for routing and navigation between different views in the React application.
- **React Webcam**: A React component for accessing and displaying webcam feeds, used for video capture in the assembly monitoring process.
- **Simple Statistics**: A statistics library for performing data analysis and calculations like mean, median, mode, etc.

### Development Dependencies:
- **@eslint/js**: ESLint configuration for linting JavaScript code.
- **@types/react**: TypeScript type definitions for React.
- **@types/react-dom**: TypeScript type definitions for React DOM.
- **@vitejs/plugin-react**: Vite plugin for React, enabling faster development builds.
- **ESLint**: A tool for identifying and fixing problems in JavaScript/TypeScript code.
- **ESLint Plugin for React Hooks**: Provides linting rules for React hooks.
- **ESLint Plugin for React Refresh**: Provides linting rules related to React's fast refresh during development.
- **Globals**: Adds global variables support for ESLint.
- **TypeScript**: A typed superset of JavaScript, enabling better tooling and type-checking during development.
- **TypeScript-ESLint**: TypeScript support for ESLint, enabling linting in TypeScript files.
- **Vite**: A next-generation build tool for frontend development, ensuring fast build and development times.
  


## Setup

Follow the steps below to set up the **Video Assembly Monitor Web** frontend project. We recommend using **WebStorm** for importing and managing the project for a smooth development experience.

**Before setup frontend app, setup backend app first.**
### 1. Clone the Repository

Start by cloning the project repository from GitHub.
Download the whole project, and unzip the file to a place you like.

### 2. Open the Project in WebStorm

1. Open **WebStorm**, which you can download [here](https://www.jetbrains.com/webstorm/download/#section=windows).
2. On the welcome screen, select **Open**.
3. Navigate to the folder where you unzip the repository file, and select the project directory.
4. WebStorm will automatically detect the project configuration and suggest installing necessary dependencies. Click **Install** to ensure all dependencies are installed.
5. If you miss the hint that let you download **Node.js**, you can download [here](https://nodejs.org/).
6. If you miss the hint that let you install the dependencies, follow the **Install Dependencies** to get all dependencies set.

### 3. Install Dependencies

After importing the project, run the following command in the WebStorm terminal to install the necessary dependencies:

```bash
npm install
```

Or, you don't want to use terminal, you can follow:

1. In WebStorm, open the **Run/Debug Configurations** dialog by clicking on the **Run** dropdown in the top-right corner and selecting **Edit Configurations**.
2. Click on the **+** icon and select **npm**.
3. In the **command** field, select **install**.
4. Click **OK** and then click the **Run** button (green triangle) in the top-right corner of the IDE.

This will install both the core dependencies and development dependencies specified in `package.json`.

### 4. Start the Development Server

After the dependencies are installed, start the development server using the following command:

```bash
npm run dev
```

Or, you don't want to use terminal, you can follow:

1. In WebStorm, open the **Run/Debug Configurations** dialog by clicking on the **Run** dropdown in the top-right corner and selecting **Edit Configurations**.
2. Click on the **+** icon and select **npm**.
3. In the **command** field, select **run**.
4. In the **script** field, select **dev**.
5. Click **OK** and then click the **Run** button (green triangle) in the top-right corner of the IDE.

This will start the Vite development server, and the project will automatically open in your default web browser. The app will hot reload as you make changes to the code.

### 5. Build the Project for Production

To build the project for production, run the following command:

```bash
npm run build
```

Or, you don't want to use terminal, you can follow:

1. In WebStorm, open the **Run/Debug Configurations** dialog by clicking on the **Run** dropdown in the top-right corner and selecting **Edit Configurations**.
2. Click on the **+** icon and select **npm**.
3. In the **command** field, select **run**.
4. In the **script** field, select **build**.
5. Click **OK** and then click the **Run** button (green triangle) in the top-right corner of the IDE.

This will generate an optimized build of the frontend, ready for deployment, in the `dist/` directory.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This project would not have been possible without the support and contributions from the following:

- **Supervisor**: Special thanks to my supervisor, Ong SohKhim, for the invaluable guidance and feedback throughout the development of this project.
- **Teammate**: Thanks to my teammate, Cai Yunchen, for building the model and other help.
- **Previous Researchers**: For providing a general methodology, dataset, model and optimization ideas for this project.
- **Libraries & Frameworks**:
  - **YOLO**: For providing an efficient object detection algorithm that powers the real-time object recognition in the assembly process.
  - **MediaPipe**: For enabling precise hand gesture recognition that enhances the user interaction with the system.
  - **OpenCV**: For serving as the core computer vision library that enables video processing and object detection tasks.
  - **Spring Boot**: For offering a powerful framework for building the backend services of the project with minimal configuration.
  - **Vite**: For providing a fast and optimized build tool that supports the frontend of the project.
  - **React**: For offering a component-based architecture that makes building the frontend intuitive and maintainable.
  - **Ant Design**: For supplying high-quality UI components that contributed to the smooth user interface design.
  - **MySQL**: For providing the database support to manage and store assembly process data.
  - **Gradle**: For automating the build and dependency management of the project.
  - **JUnit**: For helping ensure the backend code is thoroughly tested and reliable.
- **Everyone who provided feedback**: Your insights helped improve the quality and direction of this project.

This project is part of my **FYP (Final Year Project)** at NUSRI@Suzhou and Chongqing University, and other acknowledgments will be listed in my **CA2 Report**.

---

For further information, please refer to the provided links for REST API documentation.

If you have any questions or suggestions, feel free to open an issue on the [GitHub repository](https://github.com/LtSeed/VideoAssemblyMonitorWeb).

