import React, { useEffect, useState } from "react";
import { Toast, Button, ToastContainer } from "react-bootstrap";

type ConnectionToastProps = {
  connectionStatus: string;
};

/**
 * ConnectionToast Component
 *
 * Displays a toast notification that reflects the current connection status.
 *
 * Props:
 * - connectionStatus (string): The current status of the connection which can be
 *   'connecting', 'connected', 'disconnected', or 'reconnecting'. The component uses this
 *   status to determine the message, background color (`bg`), and auto-hide delay of the toast.
 *
 * The toast is designed to automatically appear based on changes to the `connectionStatus` prop
 * and provides a close button to manually dismiss the toast. It uses `react-bootstrap`'s Toast
 * component to show the connection status in a stylized format, and Bootstrap's utility classes
 * for alignment and spacing.
 */
export const ConnectionToast = React.memo(
  ({ connectionStatus }: ConnectionToastProps) => {
    const [show, setShow] = useState(true);

    useEffect(() => {
      setShow(true);
    }, [connectionStatus]);

    const handleClose = () => setShow(false);

    const getToastContent = (): {
      message: string;
      bg: string; // bootstrap uses `bg` prop for background color
      delay: number | undefined;
    } => {
      switch (connectionStatus) {
        case "connecting":
          return {
            message: "Connecting...",
            bg: "info",
            delay: undefined,
          };
        case "connected":
          return { message: "Connected", bg: "success", delay: 1000 };
        case "disconnected":
          return {
            message: "Disconnected",
            bg: "danger",
            delay: undefined,
          };
        case "reconnecting":
          return {
            message: "Reconnecting...",
            bg: "info",
            delay: undefined,
          };
        default:
          return {
            message: "",
            bg: "info",
            delay: undefined,
          };
      }
    };

    const { message, bg, delay } = getToastContent();

    return (
      <ToastContainer position="bottom-center" className="toastContainer">
        <Toast
          show={show}
          onClose={handleClose}
          delay={delay}
          autohide={delay !== undefined}
          bg={bg}>
          <Toast.Body className="d-flex justify-content-between">
            {message}
            <Button variant="close" size="sm" onClick={handleClose} />
          </Toast.Body>
        </Toast>
      </ToastContainer>
    );
  },
);

ConnectionToast.displayName = "ConnectionToast";
