import React from 'react';
import { ToastContainer, Toast } from 'react-bootstrap';

export type Notification = {
  id: number;
  time: string;
  text: string;
};

type NotificationProps = {
  showNotification: boolean;
  notifications: Notification[];
  exceptions: Notification[];
  removeNotificationById: (id: number) => void;
  removeExceptionById: (id: number) => void;
};

export const Notifications = React.memo((props: NotificationProps) => {
  const {
    showNotification,
    notifications,
    exceptions,
    removeExceptionById,
    removeNotificationById
  } = props;

  return (
    <ToastContainer className="navbarOffset toastContainer" position="top-end">
      {showNotification &&
        notifications.map((notification) => (
          <Toast
            className="notificationToast"
            key={notification.id}
            onClose={() => removeNotificationById(notification.id)}
            onClick={() => {
              removeNotificationById(notification.id);
            }}
            onMouseLeave={() => {
              removeNotificationById(notification.id);
            }}
            show={true}
            autohide={true}
            delay={2000}>
            <Toast.Header closeButton={false} className="notificationToast text-right">
              <strong className="me-auto">Notification</strong>
              <small>{notification.time}</small>
            </Toast.Header>
            <Toast.Body>{notification.text}</Toast.Body>
          </Toast>
        ))}
      {exceptions.map((exception) => (
        <Toast
          className="exceptionToast"
          key={exception.id}
          onClose={() => removeExceptionById(exception.id)}
          onClick={() => {
            removeExceptionById(exception.id);
          }}
          show={true}
          autohide={false}>
          <Toast.Header closeButton className="exceptionToast text-right">
            <strong className="me-auto">Exception</strong>
            <small>{exception.time}</small>
          </Toast.Header>
          <Toast.Body>{exception.text}</Toast.Body>
        </Toast>
      ))}
    </ToastContainer>
  );
});
