# Expedition Ticket System Updates - January 20, 2025

## Updates Applied

### 1. Forgotten Role Ping System
- **New Feature**: Added ability to ping a specific "forgotten role" when tickets are created
- **Command Added**: `/set_forgotten_role` - Allows administrators to set which role gets pinged
- **Functionality**: When a ticket is created, the forgotten role receives a notification with ticket details

### 2. Updated Ticket Descriptions

#### Player Report
- **Old Title**: `🛡️ Player Report`
- **New Title**: `🛡️ Player Report (In Expedition Antarctica)`
- **Updated Description**: "Report other players for using a third-party software (exploits) to gain an unfair advantage. Provide us with sufficient evidence to help us review the report and take appropriate action, preferably video files. Players that are banned for cheating cannot appeal, unless their innocence is proven."

#### Bug Report
- **Updated Description**: "Is something not working as intended and it needs immediate attention from the developers? Report it and ensure to include sufficient details to help us identify and resolve the issue."

### 3. Panel Updates
- Updated main ticket panel to reflect new descriptions
- Added clarification about cheating ban appeals in the guidelines
- Improved overall messaging consistency

## New Commands

### `/set_forgotten_role <role>`
- **Permission**: Administrator only
- **Description**: Set the role that gets pinged when new tickets are created
- **Usage**: `/set_forgotten_role @Support Team`
- **Effect**: The specified role will be pinged with a notification embed whenever a new ticket is created

## Technical Implementation

### Forgotten Role System
1. **Storage**: Role ID stored in `self.forgotten_role_id`
2. **Permissions**: Forgotten role automatically gets read/send permissions in ticket channels
3. **Notification**: Separate embed sent after ticket creation with role ping
4. **Format**: 
   ```
   @ForgottenRole
   🔔 New Ticket Created
   A new [Ticket Type] ticket has been created by @User
   **Ticket:** #ticket-channel
   **Type:** Ticket Type Name
   **User:** @User
   ```

### Updated Ticket Flow
1. User clicks ticket button
2. Ticket channel is created with proper permissions
3. Initial ticket embed is sent
4. **NEW**: If forgotten role is set, notification embed is sent with role ping
5. User receives confirmation message

## Configuration Required

After deployment, administrators need to:
1. Use `/set_forgotten_role @RoleName` to configure which role gets pinged
2. Ensure the role has appropriate permissions in the server
3. Test ticket creation to verify pings work correctly

## Benefits
- **Improved Response Time**: Forgotten role gets immediate notification of new tickets
- **Better Organization**: Clear identification of Expedition Antarctica context
- **Enhanced Clarity**: Updated descriptions provide clearer guidance to users
- **Flexible Configuration**: Administrators can change the pinged role as needed

## Files Modified
- `cogs/expedition_tickets.py` - Updated ticket system with new functionality
- `deployment_trigger.txt` - Triggered deployment
- `EXPEDITION_TICKET_UPDATES.md` - This documentation file