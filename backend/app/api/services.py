"""
Services management endpoints
Docker container status, logs, and control
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
import subprocess
import os
from .. import auth_utils
from ..models import User

router = APIRouter()


def get_docker_compose_command():
    """Determine docker-compose command (v1 or v2)"""
    try:
        subprocess.run(['docker-compose', '--version'], capture_output=True, check=True)
        return 'docker-compose'
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(['docker', 'compose', 'version'], capture_output=True, check=True)
            return 'docker compose'
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None


@router.get('/services/status')
async def get_services_status(
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get status of all Docker containers/services
    Requires admin privileges
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    docker_cmd = get_docker_compose_command()
    if not docker_cmd:
        return {
            'error': 'Docker Compose not available',
            'services': [],
            'stats': {'total': 0, 'running': 0, 'exited': 0}
        }
    
    try:
        # Get docker-compose service status
        cmd = docker_cmd.split() + ['ps', '--format', 'json']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd='/home/ubuntu/fastapi-bizcard-crm-ready'  # Adjust path as needed
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to get services status: {result.stderr}")
        
        # Parse output
        import json
        services = []
        running_count = 0
        exited_count = 0
        
        # Split by lines and parse each as JSON
        lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        for line in lines:
            try:
                service_data = json.loads(line)
                service_name = service_data.get('Service', service_data.get('Name', 'unknown'))
                state = service_data.get('State', 'unknown')
                
                # Categorize service
                category = 'other'
                if service_name in ['backend', 'frontend', 'postgres', 'redis']:
                    category = 'core'
                elif service_name in ['celery', 'celery-beat']:
                    category = 'processing'
                elif service_name in ['prometheus', 'grafana']:
                    category = 'monitoring'
                
                # Format ports properly
                publishers = service_data.get('Publishers', [])
                ports_str = ''
                if publishers and isinstance(publishers, list):
                    try:
                        ports_str = ', '.join([f"{p.get('PublishedPort', '')}:{p.get('TargetPort', '')}" for p in publishers if isinstance(p, dict)])
                    except:
                        ports_str = str(publishers)
                
                services.append({
                    'name': service_name,
                    'state': state.lower(),  # Changed from 'status' to 'state' for consistency
                    'status': state.lower(),
                    'category': category,
                    'ports': ports_str,
                    'image': service_data.get('Image', ''),
                    'created': service_data.get('CreatedAt', ''),
                    'running_for': service_data.get('RunningFor', '')
                })
                
                if state.lower() == 'running':
                    running_count += 1
                elif state.lower() in ['exited', 'stopped']:
                    exited_count += 1
                    
            except json.JSONDecodeError:
                continue
        
        # If no services found from JSON, try legacy format
        if not services:
            cmd = docker_cmd.split() + ['ps']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd='/home/ubuntu/fastapi-bizcard-crm-ready'
            )
            
            # Parse table format (legacy)
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 4:
                    service_name = parts[0].replace('fastapi-bizcard-crm-ready-', '')
                    state = 'running' if 'Up' in line else 'exited'
                    
                    category = 'other'
                    if service_name in ['backend', 'frontend', 'postgres', 'redis']:
                        category = 'core'
                    elif service_name in ['celery', 'celery-beat']:
                        category = 'processing'
                    elif service_name in ['prometheus', 'grafana']:
                        category = 'monitoring'
                    
                    services.append({
                        'name': service_name,
                        'status': state,
                        'category': category
                    })
                    
                    if state == 'running':
                        running_count += 1
                    else:
                        exited_count += 1
        
        # Categorize services for frontend
        categorized = {}
        for service in services:
            cat = service['category']
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(service)
        
        return {
            'services': services,
            'categorized': categorized,
            'stats': {
                'total': len(services),
                'running': running_count,
                'exited': exited_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting services status: {str(e)}")


@router.post('/services/{service_name}/restart')
async def restart_service(
    service_name: str,
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Restart a specific Docker service
    Requires admin privileges
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    docker_cmd = get_docker_compose_command()
    if not docker_cmd:
        raise HTTPException(status_code=500, detail="Docker Compose not available")
    
    try:
        cmd = docker_cmd.split() + ['restart', service_name]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd='/home/ubuntu/fastapi-bizcard-crm-ready',
            timeout=60
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to restart service: {result.stderr}")
        
        return {
            'status': 'success',
            'message': f'Service {service_name} restarted successfully',
            'output': result.stdout
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Service restart timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restarting service: {str(e)}")


@router.get('/services/{service_name}/logs')
async def get_service_logs(
    service_name: str,
    lines: int = 100,
    current_user: User = Depends(auth_utils.get_current_active_user)
):
    """
    Get logs for a specific Docker service
    Requires admin privileges
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    docker_cmd = get_docker_compose_command()
    if not docker_cmd:
        raise HTTPException(status_code=500, detail="Docker Compose not available")
    
    try:
        cmd = docker_cmd.split() + ['logs', '--tail', str(lines), service_name]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd='/home/ubuntu/fastapi-bizcard-crm-ready',
            timeout=30
        )
        
        return {
            'service': service_name,
            'logs': result.stdout + result.stderr,
            'lines': lines
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Logs retrieval timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

