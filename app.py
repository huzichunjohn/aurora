
@app.route('/ansible/role/', method=['POST'])
def role():
	inst_ip = request.form['host']
	inst_role = request.form['role']
	env = request.form['env']
	ans_remote_user = 'ubuntu'
	ans_private_key = '/home/ubuntu/.ssh/id_rsa'
	job = q.enqueue_call(
			func=ansble_run, args=(inst_ip, inst_role, env, ans_remote_user, ans_private_key,), result_ttl=5000, timeout=2000
		)
	return job.get_id()

def gen_pbook_yml(ip, role):
	r_text = ''
	templateLoader = jinja2.FileSystemLoader(searchpath='/')
	templateEnv = jinja2.Environment(loader=templateLoader)
	TEMPLATE_FILE = "/opt/ansible/playbook.jinja"
	template = templateEnv.get_template(TEMPLATE_FILE)
	role = role.split(',')
	r_text = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
	temp_file = "/tmp/" + "ans-" + r_text + ".yml"
	templateVars = {
		'hst': ip,
		'roles': role
	}
	outputText = template.render(templateVars)
	text_file = open(temp_file, "w")
	text_file.write(outputText)
	text_file.close()
	return temp_file

def ansble_run(ans_inst_ip, ans_inst_role, ans_env, ans_user, ans_key_file):
	yml_pbook = gen_pbook_yml(ans_inst_ip, ans_inst_role)
	run_pbook = ansible.playbook.PlayBook(
		playbook=yml_pbook,
		callbacks=playbook_cb,
		runner_callbacks=runner_cb,
		stats=stats,
		remote_user=ans_user,
		private_key_file=ans_key_file,
		host_list="/etc/ansible/hosts",
		extra_vars={
			'env': ans_env
		}
		).run()
	return run_pbook

@app.route("/ansible/results/<job_key>", methods=['GET'])
def get_results(job_key):
	job = Job.fetch(job_key, connection=conn)
	if job.is_finished:
		ret = job.return_value
	elif job.is_queued:
		ret = {'status': 'in-queue'}
	elif job.is_started:
		ret = {'status': 'waiting'}
	elif job.is_failed:
		ret = {'status': 'failed'}
	return json.dumps(ret), 200