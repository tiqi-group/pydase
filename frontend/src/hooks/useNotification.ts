import { useState } from 'react';
import { Notification } from '../components/NotificationsComponent';

export const useNotification = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const notify = (text: string) => {
    // Getting the current time in the required format
    const timeString = new Date().toISOString().substring(11, 19);
    // Adding an id to the notification to provide a way of removing it
    const id = Math.random();

    // Custom logic for notifications
    setNotifications((prevNotifications) => [
      { id, text, time: timeString },
      ...prevNotifications
    ]);
  };

  const removeNotificationById = (id: number) => {
    setNotifications((prevNotifications) =>
      prevNotifications.filter((n) => n.id !== id)
    );
  };

  return { notifications, notify, removeNotificationById };
};
