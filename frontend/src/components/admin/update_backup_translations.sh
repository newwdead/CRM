#!/bin/bash
# Update BackupManagement.js with translations

FILE="BackupManagement.js"

# Toast messages
sed -i "s/toast\.success('Backup system test successful')/toast.success(t.testSuccessful)/g" "$FILE"
sed -i "s/toast\.error('Backup system test failed')/toast.error(t.testFailed)/g" "$FILE"
sed -i "s/toast\.error('Failed to test backup')/toast.error(t.failedTest)/g" "$FILE"
sed -i "s/toast\.error('Failed to create backup')/toast.error(t.failedCreateBackup)/g" "$FILE"
sed -i "s/toast\.success('Backup created successfully:')/toast.success(t.backupCreated + ':')/g" "$FILE"
sed -i "s/'Are you sure you want to delete this backup?'/t.confirmDeleteBackup/g" "$FILE"
sed -i "s/toast\.success('Backup deleted successfully')/toast.success(t.backupDeleted)/g" "$FILE"
sed -i "s/toast\.error('Failed to delete backup')/toast.error(t.failedDeleteBackup)/g" "$FILE"

# UI texts
sed -i "s/>💾 Backup & Recovery</>💾 {t.backupTitle}</g" "$FILE"
sed -i "s/Manage database backups, configure automatic backup schedule, and recovery options/{t.backupSubtitle}/g" "$FILE"
sed -i "s/>⚙️ Automatic Backup Configuration</>⚙️ {t.automaticBackupConfig}</g" "$FILE"
sed -i "s/>Backup Schedule (cron)</{t.backupSchedule}/g" "$FILE"
sed -i "s/>Retention Days</{t.retentionDays}/g" "$FILE"
sed -i "s/0 2 \* \* \* (daily at 2 AM)/{t.scheduleExample}/g" "$FILE"
sed -i "s/>Enabled</{t.enabledStatus}/g" "$FILE"
sed -i "s/>Disabled</{t.disabledStatus}/g" "$FILE"
sed -i "s/>Test Backup System</{t.testConnection}/g" "$FILE"
sed -i "s/>Edit Configuration</{t.editConfig}/g" "$FILE"
sed -i "s/>📦 Manual Backups</>📦 {t.manualBackups}</g" "$FILE"
sed -i "s/Create backups manually or manage existing backup files/{t.manualBackupsDesc}/g" "$FILE"
sed -i "s/>Create Backup Now</{t.createBackupNow}/g" "$FILE"
sed -i "s/>Creating\.\.\.</{t.creating}/g" "$FILE"
sed -i "s/>📦 Available Backups</>📦 {t.availableBackups}</g" "$FILE"
sed -i "s/>Filename</{t.filename}/g" "$FILE"
sed -i "s/>Size</{t.size}/g" "$FILE"
sed -i "s/>Created</{t.created}/g" "$FILE"
sed -i "s/>Actions</{t.actions}/g" "$FILE"
sed -i "s/>Download</{t.download}/g" "$FILE"
sed -i "s/>Delete</{t.delete}/g" "$FILE"
sed -i "s/No backups found\. Click "Create Backup Now" to create your first backup\./{t.noBackupsFound}/g" "$FILE"
sed -i "s/>Save</{t.save}/g" "$FILE"
sed -i "s/>Cancel</{t.cancel}/g" "$FILE"

echo "✅ BackupManagement.js updated with translations"
