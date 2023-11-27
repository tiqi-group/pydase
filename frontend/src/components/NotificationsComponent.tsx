import React from 'react';
import { ToastContainer, Toast } from 'react-bootstrap';

export type LevelName = 'ERROR' | 'WARNING' | 'INFO' | 'DEBUG'; // Added levelname
export type Notification = {
  id: number;
  timeStamp: string;
  message: string;
  levelname: LevelName;
};

type NotificationProps = {
  showNotification: boolean;
  notifications: Notification[];
  removeNotificationById: (id: number) => void;
};

export const Notifications = React.memo((props: NotificationProps) => {
  const { showNotification, notifications, removeNotificationById } = props;

  return (
    <ToastContainer className="navbarOffset toastContainer" position="top-end">
      {showNotification &&
        notifications.map((notification) => (
          <Toast
            className={notification.levelname.toLowerCase() + 'Toast'}
            key={notification.id}
            onClose={() => removeNotificationById(notification.id)}
            onClick={() => removeNotificationById(notification.id)}
            onMouseLeave={() => {
              if (notification.levelname !== 'ERROR') {
                removeNotificationById(notification.id);
              }
            }}
            show={true}
            autohide={
              notification.levelname === 'WARNING' ||
              notification.levelname === 'INFO' ||
              notification.levelname === 'DEBUG'
            }
            delay={
              notification.levelname === 'WARNING' ||
              notification.levelname === 'INFO' ||
              notification.levelname === 'DEBUG'
                ? 2000
                : undefined
            }>
            <Toast.Header
              closeButton={false}
              className={notification.levelname.toLowerCase() + 'Toast text-right'}>
              <strong className="me-auto">{notification.levelname}</strong>
              <small>{notification.timeStamp}</small>
            </Toast.Header>
            <Toast.Body>{notification.message}</Toast.Body>
          </Toast>
        ))}
    </ToastContainer>
  );
});
