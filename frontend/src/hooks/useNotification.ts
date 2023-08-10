import { useState } from 'react';
type NotificationMsg = {
  id: number;
  time: string;
  text: string;
};

export const useNotification = () => {
  const [notifications, setNotifications] = useState([]);

  const notify = (message: NotificationMsg) => {
    // Custom logic for notifications
    setNotifications((prevNotifications) => [message, ...prevNotifications]);
  };

  const removeNotificationById = (id: number) => {
    setNotifications((prevNotifications) =>
      prevNotifications.filter((n) => n.id !== id)
    );
  };

  return { notifications, notify, removeNotificationById };
};
